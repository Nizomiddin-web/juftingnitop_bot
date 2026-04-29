from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import DB_URL
from bot.database.models import Base

engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Eski SQLite jadvallarga yangi ustunlar qo'shish (lightweight migration).
USER_COLUMN_MIGRATIONS = [
    ("notifications_on", "BOOLEAN DEFAULT 1"),
    ("is_banned", "BOOLEAN DEFAULT 0"),
    ("is_verified", "BOOLEAN DEFAULT 0"),
    ("created_at", "VARCHAR"),
    ("phone", "VARCHAR(20)"),
    ("role", "VARCHAR(20) DEFAULT 'user'"),
    ("nationality", "VARCHAR(50)"),
    ("religion_level", "VARCHAR(50)"),
    ("prays", "VARCHAR(20)"),
    ("wears_hijab", "VARCHAR(20)"),
    ("last_active", "VARCHAR"),
    ("search_education", "VARCHAR(100)"),
    ("about_me", "TEXT"),
    ("intention_period", "VARCHAR(50)"),
    ("profession", "VARCHAR(100)"),
    ("education_level", "VARCHAR(100)"),
    ("marital_status", "VARCHAR(100)"),
    ("region", "VARCHAR(100)"),
    ("district", "VARCHAR(100)"),
    ("latitude", "FLOAT"),
    ("longitude", "FLOAT"),
    ("search_age_min", "INTEGER DEFAULT 18"),
    ("search_age_max", "INTEGER DEFAULT 35"),
    ("search_distance_km", "INTEGER DEFAULT 50"),
]


REPORT_COLUMN_MIGRATIONS = [
    ("is_resolved", "BOOLEAN DEFAULT 0"),
]


async def _migrate_table(conn, table: str, columns: list[tuple[str, str]]) -> None:
    res = await conn.execute(text(f"PRAGMA table_info({table})"))
    existing = {row[1] for row in res.fetchall()}
    for col, ddl in columns:
        if col not in existing:
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if DB_URL.startswith("sqlite"):
            await _migrate_table(conn, "users", USER_COLUMN_MIGRATIONS)
            await _migrate_table(conn, "reports", REPORT_COLUMN_MIGRATIONS)
