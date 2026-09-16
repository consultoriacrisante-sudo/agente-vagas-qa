import os
import requests

from src.models import Job


def format_job(job: Job) -> str:
    icon = "🧪" if job.track == "qa" else "☁️"
    track = "QA" if job.track == "qa" else "SALESFORCE — INÍCIO DE CARREIRA"
    skills = ", ".join(job.matched_skills[:6]) or "aderência pelo cargo/descrição"
    return (
        f"{icon} <b>{track}</b>\n"
        f"🎯 Match {job.match_score}%\n"
        f"💼 <b>{job.title}</b>\n"
        f"🏢 {job.company}\n"
        f"🌎 100% REMOTO\n"
        f"📝 {job.employment_type}\n"
        f"✅ {skills}\n"
        f"🔗 <a href=\"{job.url}\">VER VAGA</a>"
    )


def send_job(job: Job) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": format_job(job),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    response.raise_for_status()
