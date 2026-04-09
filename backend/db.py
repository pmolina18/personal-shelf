"""SQLAlchemy async engine and session configuration."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import DATABASE_URL, is_neon_db

connect_args = {"ssl": "require"} if is_neon_db() else {}
engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Yield an async database session."""
    async with async_session() as session:
        yield session
