import os

import requests
from flask import Flask, jsonify, request

from src.profile_extractor import extract_candidate_profile
from src.resume import extract_resume_text

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


def send_message(chat_id: int, text: str):
    return telegram_api("sendMessage", {"chat_id": chat_id, "text": text})


def download_telegram_file(file_id: str) -> bytes:
    metadata = telegram_api("getFile", {"file_id": file_id})
    file_path = metadata["result"]["file_path"]
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    response = requests.get(
        f"https://api.telegram.org/file/bot{token}/{file_path}", timeout=30
    )
    response.raise_for_status()
    return response.content


def handle_document(chat_id: int, document: dict):
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

    skills = ", ".join(profile["skills"][:12]) or "perfil profissional identificado"
    years = profile["years_experience"] or "não informado"
    send_message(
        chat_id,
        f"✅ Currículo {filename} analisado.\n\n"
        f"🧠 Skills identificadas: {skills}\n"
        f"⏱ Experiência: {years} anos\n"
        f"🎯 Senioridade: {profile['seniority']}\n\n"
        "Agora seu perfil pode ser usado para calcular a compatibilidade das vagas."
    )
    # Persistência do perfil será ligada ao storage multiusuário no próximo estágio.
    return profile


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "agente-vagas-qa"})


@app.post("/telegram/webhook")
def telegram_webhook():
    expected_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
    if expected_secret:
        received = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if received != expected_secret:
            return jsonify({"ok": False}), 401

    update = request.get_json(silent=True) or {}
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if not chat_id:
        return jsonify({"ok": True})

    text = (message.get("text") or "").strip().lower()
    if text in {"/start", "/perfil", "/curriculo"}:
        send_message(chat_id, WELCOME)
    elif message.get("document"):
        handle_document(chat_id, message["document"])
    else:
        send_message(chat_id, "📎 Envie seu currículo em PDF ou DOCX para começar.")

    return jsonify({"ok": True})
