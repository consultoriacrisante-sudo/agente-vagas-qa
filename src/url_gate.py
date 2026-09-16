from urllib.parse import urlparse


def valid_application_url(url: str) -> bool:
    """Only deliver vacancies with a real HTTP(S) application/job URL."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
