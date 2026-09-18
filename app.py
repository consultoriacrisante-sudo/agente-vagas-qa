import os

import requests
from flask import Flask, jsonify, request

from src.daily import deliver_jobs_for_users
from src.discovery import discover_jobs
from src.profile_extractor import extract_candidate_profile
from src.resume import MAX_RESUME_BYTES, extract_resume_text
from src.storage import JobStore

app = Flask(__name__)

WELCOME = (
    "👋 Olá! Sou seu Agente Inteligente de Vagas.\n\n"
    "📄 Anexe o seu currículo em PDF ou DOCX para que nós possamos encontrar "
    "as vagas que são compatíveis com o seu perfil.\n\n"
    "🌎 Depois do currículo, informe seu país com /pais Brasil (ou o seu país). "
    "Assim que o país for confirmado, a primeira busca começa automaticamente.\n\n"
    "🔎 Depois, use /vagas quando quiser procurar novas oportunidades."
)


def telegram_api(method: str, payload=None):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    response = requests.post(
        f"https://api.telegram.org/bot{token}/{method}", json=payload or {}, timeout=30
    )
    response.raise_for_status()
    return response.json()


def send_message(chat_id: int, text: str, parse_mode: str | None = None):
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
        payload["disable_web_page_preview"] = True
    return telegram_api("sendMessage", payload)


def download_telegram_file(file_id: str) -> bytes:
    metadata = telegram_api("getFile", {"file_id": file_id})
    file_path = metadata["result"]["file_path"]
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    response = requests.get(f"https://api.telegram.org/file/bot{token}/{file_path}", timeout=30)
    response.raise_for_status()
    return response.content


def handle_document(chat_id: int, document: dict, display_name: str = ""):
    mime = document.get("mime_type", "")
    filename = document.get("file_name", "curriculo")
    if int(document.get("file_size") or 0) > MAX_RESUME_BYTES:
        return send_message(chat_id, "⚠️ O currículo é muito grande. O limite atual é 8 MB.")

    try:
        data = download_telegram_file(document["file_id"])
        text = extract_resume_text(data, mime)
        if len(text) < 80:
            raise ValueError("resume_without_enough_text")
        profile = extract_candidate_profile(text)
        JobStore().upsert_candidate_profile(chat_id, profile, display_name, filename, mime)
    except ValueError as exc:
        if str(exc) == "unsupported_resume_type":
            return send_message(chat_id, "⚠️ Envie o currículo em PDF ou DOCX.")
        if str(exc) == "resume_too_large":
            return send_message(chat_id, "⚠️ O currículo é muito grande. O limite atual é 8 MB.")
        return send_message(chat_id, "⚠️ Não consegui extrair texto suficiente desse currículo.")
    except (requests.RequestException, KeyError, OSError):
        return send_message(chat_id, "⚠️ Não consegui processar o currículo agora. Tente enviar o arquivo novamente.")

    skills = ", ".join(profile["skills"][:12]) or "perfil profissional identificado"
    years = profile["years_experience"] if profile["years_experience"] is not None else "não informado"
    send_message(
        chat_id,
        f"✅ Currículo {filename} analisado e perfil salvo.\n\n"
        f"🧠 Skills identificadas: {skills}\n"
        f"⏱ Experiência: {years} anos\n"
        f"🎯 Senioridade: {profile['seniority']}\n\n"
        "🌎 Falta só confirmar seu país. Exemplo: /pais Brasil",
    )
    return profile


def _candidate_row(chat_id: int, store: JobStore) -> dict | None:
    return next(
        (row for row in store.list_candidate_profiles() if int(row["telegram_user_id"]) == int(chat_id)),
        None,
    )


def search_jobs_now(chat_id: int) -> None:
    store = JobStore()
    row = _candidate_row(chat_id, store)
    if not row:
        send_message(chat_id, "📄 Primeiro envie seu currículo em PDF ou DOCX.")
        return
    profile = row.get("profile") or {}
    if not profile.get("country"):
        send_message(chat_id, "🌎 Primeiro confirme seu país. Exemplo: /pais Brasil")
        return

    send_message(chat_id, "🔎 Buscando novas vagas 100% remotas compatíveis com o seu perfil...")
    try:
        jobs, _discovery = discover_jobs()
        result = deliver_jobs_for_users(jobs, store=store, only_user_id=chat_id)
    except (requests.RequestException, KeyError, OSError, RuntimeError):
        send_message(chat_id, "⚠️ Não consegui concluir a busca agora. Tente novamente em alguns minutos com /vagas.")
        return

    if result["sent"] == 0:
        send_message(
            chat_id,
            "ℹ️ Não encontrei uma vaga nova que passe por todos os filtros agora. "
            "Seu perfil continua ativo e você pode usar /vagas novamente mais tarde.",
        )


def set_country(chat_id: int, country: str) -> None:
    country = country.strip()
    if not country or len(country) > 80:
        send_message(chat_id, "⚠️ Use o formato /pais Brasil")
        return
    store = JobStore()
    row = _candidate_row(chat_id, store)
    if not row:
        send_message(chat_id, "📄 Primeiro envie seu currículo em PDF ou DOCX.")
        return
    profile = dict(row.get("profile") or {})
    profile["country"] = country
    store.upsert_candidate_profile(
        chat_id,
        profile,
        row.get("display_name") or "",
        row.get("resume_file_name") or "",
        row.get("resume_mime_type") or "",
    )
    send_message(chat_id, f"✅ País confirmado: {country}. Vou iniciar sua primeira busca agora.")
    search_jobs_now(chat_id)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "agente-vagas-qa"})


@app.get("/cron/daily")
def cron_daily():
    secret = os.environ.get("CRON_SECRET")
    authorization = request.headers.get("Authorization", "")
    if not secret or authorization != f"Bearer {secret}":
        return jsonify({"ok": False}), 401

    jobs, discovery = discover_jobs()
    result = deliver_jobs_for_users(jobs)
    return jsonify({"ok": True, "discovery": discovery, **result})


@app.post("/telegram/webhook")
def telegram_webhook():
    expected_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
    if expected_secret and request.headers.get("X-Telegram-Bot-Api-Secret-Token") != expected_secret:
        return jsonify({"ok": False}), 401

    update = request.get_json(silent=True) or {}
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    chat_id = chat.get("id")
    if not chat_id:
        return jsonify({"ok": True})

    display_name = " ".join(part for part in [sender.get("first_name", ""), sender.get("last_name", "")] if part).strip()
    raw_text = (message.get("text") or "").strip()
    text = raw_text.lower()
    if text in {"/start", "/perfil", "/curriculo"}:
        send_message(chat_id, WELCOME)
    elif text.startswith("/pais"):
        set_country(chat_id, raw_text[5:].strip())
    elif text == "/vagas":
        search_jobs_now(chat_id)
    elif message.get("document"):
        handle_document(chat_id, message["document"], display_name)
    else:
        send_message(chat_id, "📎 Envie seu currículo em PDF ou DOCX para começar. Depois use /vagas para buscar oportunidades.")
    return jsonify({"ok": True})
