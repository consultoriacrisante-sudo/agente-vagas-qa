import os

import requests
from flask import Flask, jsonify, request

from src.daily import deliver_jobs_for_users
from src.profile_extractor import extract_candidate_profile
from src.resume import extract_resume_text
from src.storage import JobStore

app = Flask(__name__)

WELCOME = (
    "👋 Olá! Sou seu Agente Inteligente de Vagas.\n\n"
    "📄 Anexe o seu currículo em PDF ou DOCX para que nós possamos encontrar "
    "as vagas que são compatíveis com o seu perfil.\n\n"
    "🔎 Priorizamos vagas 100% remotas no Brasil e também oportunidades "
    "internacionais que aceitem profissionais do Brasil."
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
    try:
        data = download_telegram_file(document["file_id"])
        text = extract_resume_text(data, mime)
        if len(text) < 80:
            raise ValueError("resume_without_enough_text")
        profile = extract_candidate_profile(text)
    except ValueError as exc:
        if str(exc) == "unsupported_resume_type":
            return send_message(chat_id, "⚠️ Envie o currículo em PDF ou DOCX.")
        if str(exc) == "resume_too_large":
            return send_message(chat_id, "⚠️ O currículo é muito grande. O limite atual é 8 MB.")
        return send_message(chat_id, "⚠️ Não consegui extrair texto suficiente desse currículo.")

    JobStore().upsert_candidate_profile(chat_id, profile, display_name, filename, mime)
    skills = ", ".join(profile["skills"][:12]) or "perfil profissional identificado"
    years = profile["years_experience"] or "não informado"
    send_message(chat_id, f"✅ Currículo {filename} analisado e perfil salvo.\n\n🧠 Skills identificadas: {skills}\n⏱ Experiência: {years} anos\n🎯 Senioridade: {profile['seniority']}\n\nA partir de agora o agente pode usar seu perfil para selecionar vagas compatíveis.")
    return profile


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "agente-vagas-qa"})


@app.get("/cron/daily")
def cron_daily():
    secret = os.environ.get("CRON_SECRET")
    authorization = request.headers.get("Authorization", "")
    if not secret or authorization != f"Bearer {secret}":
        return jsonify({"ok": False}), 401

    # Discovery providers feed this list. Empty is safe: the cron never invents vacancies.
    result = deliver_jobs_for_users([])
    return jsonify({"ok": True, **result})


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
    text = (message.get("text") or "").strip().lower()
    if text in {"/start", "/perfil", "/curriculo"}:
        send_message(chat_id, WELCOME)
    elif message.get("document"):
        handle_document(chat_id, message["document"], display_name)
    else:
        send_message(chat_id, "📎 Envie seu currículo em PDF ou DOCX para começar.")
    return jsonify({"ok": True})
