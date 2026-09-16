from html import escape

from src.models import Job


WELCOME = (
    "👋 <b>Agente Inteligente de Vagas</b>\n\n"
    "📄 Anexe seu currículo em <b>PDF ou DOCX</b> para analisarmos seu perfil "
    "e encontrarmos vagas compatíveis com sua experiência.\n\n"
    "🇧🇷 Vagas do Brasil têm prioridade. Também podemos apresentar oportunidades "
    "internacionais 100% remotas quando forem elegíveis para candidatos no Brasil."
)


def vacancy_message(job: Job) -> str:
    track = "QA" if job.track == "qa" else "Salesforce"
    contract = escape(job.employment_type or "Não informado")
    return (
        f"🎯 <b>{escape(job.title)}</b>\n"
        f"🏢 {escape(job.company)}\n"
        f"🌎 {escape(job.location or 'Remoto')}\n"
        f"🧭 Trilha: {track}\n"
        f"📄 Contratação: {contract}\n"
        f"📊 Match Score: <b>{job.match_score}/100</b>\n\n"
        f"🔗 <a href=\"{escape(job.url, quote=True)}\">Ver vaga e candidatar-se</a>"
    )
