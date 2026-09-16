import hashlib
import re
from urllib.parse import urlsplit, urlunsplit


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    path = re.sub(r"/+$", "", parts.path)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def job_fingerprint(source_id: str, company: str, title: str, location: str, url: str) -> str:
    if source_id:
        raw = f"source:{source_id.strip().lower()}"
    else:
        normalized = "|".join(
            re.sub(r"\s+", " ", value.strip().lower())
            for value in (company, title, location, canonical_url(url))
        )
        raw = normalized
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
