import html
import os
from urllib.parse import urlparse

import requests

from src.models import Job


def _valid_application_url(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def format_job(job: Job) -> str:
    if not _valid_application_url(job.url):
        raise ValueError("Vaga sem URL válida de candidatura")

    icon = "🧪" if job.track == "qa" else "☁️"
    track = "QA" if job.track == "qa" else "SALESFORCE — INÍCIO DE CARREIRA"
    skills = ", ".join(job.matched_skills[:6]) or "aderência pelo cargo/descrição"
    contract = job.employment_type or "Não informado"

    return (
        f"{icon} <b>{track}</b>\n"
        f"🎯 Match {job.match_score}%\n"
        f"💼 <b>{html.escape(job.title)}</b>\n"
        f"🏢 {html.escape(job.company)}\n"
        f"📍 {html.escape(job.location or 'Não informada')}\n"
        f"🌎 100% REMOTO\n"
        f"📝 Contratação: {html.escape(contract)}\n"
        f"✅ {html.escape(skills)}\n\n"
        "👇 <b>Candidatura</b>"
    )


def send_job(job: Job, chat_id: str | int | None = None) -> None:
    if not _valid_application_url(job.url):
        raise ValueError("Vaga sem URL válida de candidatura")

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    target_chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not target_chat_id:
        raise RuntimeError("chat_id do usuário não informado")

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": target_chat_id,
            "text": format_job(job),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🔗 Ver vaga e candidatar-se", "url": job.url}
                ]]
            },
        },
        timeout=20,
    )
    response.raise_for_status()
