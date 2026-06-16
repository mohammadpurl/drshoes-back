from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _normalize_database_url(url: str) -> str:
    """Ensure async driver (asyncpg). Plain postgresql:// loads psycopg2 and fails."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _connect_args(url: str) -> dict:
    # Supabase (and most cloud Postgres) require SSL
    if "supabase.co" in url:
        return {"ssl": "require"}
    return {}


_db_url = _normalize_database_url(settings.database_url)
_connect = _connect_args(_db_url)

engine = create_async_engine(
    _db_url,
    echo=settings.debug,
    pool_pre_ping=True,
    connect_args=_connect,
)

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
