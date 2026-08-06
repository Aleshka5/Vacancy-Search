"""Database setup — async SQLAlchemy engine and session factory."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config.settings import Settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


_engine: Optional[create_async_engine] = None
_async_session_factory: Optional[sessionmaker[AsyncSession]] = None


def get_engine(settings: Settings | None = None) -> create_async_engine:
    """Get or create the async engine."""
    global _engine
    if _engine is None:
        s = settings or Settings()
        _engine = create_async_engine(s.DATABASE_URL, echo=s.APP_ENV == "development")
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        s = settings or Settings()
        _async_session_factory = sessionmaker(
            bind=get_engine(s),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


async def get_async_session() -> AsyncSession:
    """Yield an async database session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def init_db(settings: Settings | None = None) -> None:
    """Create tables (dev convenience)."""
    engine = get_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def shutdown_db() -> None:
    """Dispose the engine."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
