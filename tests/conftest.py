"""Shared fixtures for Media Tracker property tests."""

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.models.media import Base
from backend.models.user import User  # noqa: F401 — registers users table in Base.metadata
from backend.services.export_service import ExportService
from backend.services.media_service import MediaService

# In-memory SQLite for fast, isolated tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Create a fresh async engine for each test."""
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Create default test user for user_id FK
    async with eng.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO users (id, email, username, password_hash) "
                "VALUES (1, 'test@test.com', 'testuser', 'fakehash')"
            )
        )
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Yield a fresh async session backed by an in-memory SQLite database."""
    factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as sess:
        yield sess


@pytest.fixture
def media_service():
    """Return a MediaService instance."""
    return MediaService()


@pytest.fixture
def export_service():
    """Return an ExportService instance."""
    return ExportService()
