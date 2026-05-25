from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Connection pool sized for a small SRE tool; tune pool_size/max_overflow
# as query concurrency grows (e.g. burst from scheduler + API traffic).
engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # detects stale connections before use
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # avoids lazy-load errors after commit in async context
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that provides a request-scoped DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables on startup.

    In production, replace this with Alembic migrations to get
    versioned, reversible schema changes and zero-downtime deployments.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent column additions so existing DB volumes don't need to be wiped.
        # PostgreSQL's IF NOT EXISTS is safe to run on every startup.
        await conn.execute(text(
            "ALTER TABLE monitored_services "
            "ADD COLUMN IF NOT EXISTS json_path VARCHAR(500)"
        ))
        await conn.execute(text(
            "ALTER TABLE monitored_services "
            "ADD COLUMN IF NOT EXISTS expected_value VARCHAR(255)"
        ))
