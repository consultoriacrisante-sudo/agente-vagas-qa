import hashlib
import re
from urllib.parse import urlsplit, urlunsplit


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    path = re.sub(r"/+$", "", parts.path)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def job_fingerprint(
    source_id: str,
    company: str,
    title: str,
    location: str,
    url: str,
    source: str = "",
) -> str:
    """Build a stable vacancy key without colliding equal IDs from different ATSs."""
    normalized_url = canonical_url(url) if url else ""
    if normalized_url:
        raw = f"url:{normalized_url}"
    elif source_id:
        raw = f"source:{_norm(source)}:{_norm(source_id)}"
    else:
        raw = "|".join(_norm(value) for value in (company, title, location))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
