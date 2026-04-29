import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///nasib_ai.db")


def _parse_admin_ids(raw: str | None) -> set[int]:
    if not raw:
        return set()
    out = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            out.add(int(part))
    return out


ADMIN_IDS: set[int] = _parse_admin_ids(os.getenv("ADMIN_IDS"))


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS
