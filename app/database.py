import logging
import ssl
from collections.abc import AsyncGenerator
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings
from app.utils.runtime import is_local_database_url, is_serverless_runtime

logger = logging.getLogger(__name__)

_CLOUD_SSL_MARKERS = (
    "supabase.co",
    "neon.tech",
    "railway.app",
    "render.com",
    "vercel-storage.com",
    "pooler.supabase.com",
)


def _normalize_database_url(url: str) -> str:
    """Ensure async driver (asyncpg). Plain postgresql:// loads psycopg2 and fails."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _connect_args(url: str) -> dict:
    lowered = url.lower()
    args: dict = {}

    if any(marker in lowered for marker in _CLOUD_SSL_MARKERS) or (
        "sslmode=require" in lowered or "ssl=require" in lowered
    ):
        # asyncpg needs an SSL context object, not the string "require"
        args["ssl"] = ssl.create_default_context()

    # Supabase pooler (PgBouncer transaction mode) — required for serverless
    if "pooler.supabase.com" in lowered or ":6543" in lowered:
        args["statement_cache_size"] = 0

    return args


def validate_database_url() -> None:
    """Fail fast with a clear message for common Vercel misconfigurations."""
    url = settings.database_url
    if is_serverless_runtime() and is_local_database_url(url):
        raise RuntimeError(
            "DATABASE_URL روی Vercel نمی‌تواند به localhost اشاره کند. "
            "در Vercel → Settings → Environment Variables مقدار DATABASE_URL را "
            "با آدرس PostgreSQL ابری (مثلاً Neon یا Supabase) تنظیم کنید."
        )

    # Direct Supabase host (db.*.supabase.co) often fails on Vercel (IPv6).
    if is_serverless_runtime():
        host = (urlparse(url).hostname or "").lower()
        if host.startswith("db.") and host.endswith(".supabase.co"):
            logger.warning(
                "DATABASE_URL uses Supabase direct connection (%s). "
                "On Vercel use the Connection Pooler URL (port 6543) from "
                "Supabase Dashboard → Connect → Transaction pooler.",
                host,
            )


_db_url = _normalize_database_url(settings.database_url)
_connect = _connect_args(_db_url)

_engine_kwargs: dict = {
    "echo": settings.debug,
    "connect_args": _connect,
}

if is_serverless_runtime():
    # Serverless: no persistent pool between invocations
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(_db_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
