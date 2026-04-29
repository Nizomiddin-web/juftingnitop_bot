import re

# Qora ro'yxat (lowercase, partial match). Qisqa ro'yxat — kerak bo'lsa kengaytiring.
BANNED_WORDS = {
    "sex", "porn", "porno", "naked", "fuck", "f*ck",
    "qotaq", "siktir", "jalab", "qahba", "kotak",
    "amxonim", "amjon", "qotoq", "siktirimda",
}

PHONE_RE = re.compile(r"(\+?\d[\d\s\-()]{7,}\d)")
URL_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|@[A-Za-z0-9_]{4,})", re.IGNORECASE)


def has_banned_word(text: str) -> bool:
    if not text:
        return False
    low = text.lower()
    return any(w in low for w in BANNED_WORDS)


def has_phone(text: str) -> bool:
    if not text:
        return False
    return bool(PHONE_RE.search(text))


def has_url_or_handle(text: str) -> bool:
    if not text:
        return False
    return bool(URL_RE.search(text))


def filter_reason(text: str) -> str | None:
    """Returns a human-readable reason if text is blocked, else None."""
    if has_banned_word(text):
        return "Matnda nomaqbul so'zlar bor."
    if has_phone(text):
        return "Telefon raqamlarini yozish taqiqlangan."
    if has_url_or_handle(text):
        return "Havolalar va Telegram username'lari taqiqlangan."
    return None
