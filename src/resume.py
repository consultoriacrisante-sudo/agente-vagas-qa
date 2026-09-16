from io import BytesIO

from docx import Document
from pypdf import PdfReader


SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_RESUME_BYTES = 8 * 1024 * 1024


def extract_resume_text(data: bytes, mime_type: str) -> str:
    if mime_type not in SUPPORTED_MIME_TYPES:
        raise ValueError("unsupported_resume_type")
    if len(data) > MAX_RESUME_BYTES:
        raise ValueError("resume_too_large")

    stream = BytesIO(data)
    if mime_type == "application/pdf":
        reader = PdfReader(stream)
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()

    document = Document(stream)
    return "\n".join(p.text for p in document.paragraphs if p.text.strip()).strip()
