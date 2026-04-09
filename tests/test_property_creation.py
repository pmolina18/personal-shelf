# Feature: media-tracker, Property 1: Creation preserves data and assigns pending status
# Feature: media-tracker, Property 2: Rejection of invalid Media_Type
"""Property tests for media item creation and validation (Properties 1, 2).

Validates: Requirements 1.1, 1.3, 1.4, 4.3
"""

import asyncio

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import sqlalchemy as sa

from backend.models.media import Base
from backend.models.user import User  # noqa: F401 — registers users table
from backend.schemas.media import MediaCreate, MediaStatus, MediaType
from backend.services.media_service import MediaService

# -- Hypothesis strategies ---------------------------------------------------

valid_media_types = st.sampled_from(
    [MediaType.movie, MediaType.book, MediaType.series]
)

valid_media_create = st.builds(
    MediaCreate,
    title=st.text(min_size=1, max_size=100).filter(lambda t: t.strip()),
    media_type=valid_media_types,
    year=st.one_of(st.none(), st.integers(min_value=1800, max_value=2100)),
    creator=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    notes=st.one_of(st.none(), st.text(max_size=200)),
    tags=st.lists(st.text(min_size=1, max_size=50), max_size=5, unique=True),
)

invalid_media_type_strings = st.text(min_size=1, max_size=50).filter(
    lambda s: s not in {"movie", "book", "series"}
)

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


async def _fresh_session():
    """Create a throwaway in-memory DB and yield a session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO users (id, email, username, password_hash) "
                "VALUES (1, 'test@test.com', 'testuser', 'fakehash')"
            )
        )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()


# -- Property 1 --------------------------------------------------------------


@settings(max_examples=100, deadline=None)
@given(data=valid_media_create)
def test_creation_preserves_data_and_assigns_pending(data):
    """For any valid MediaCreate, the created item must contain the same
    data and have status 'pending'."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            result = await svc.create(sess, data, user_id=1)

            assert result.title == data.title
            assert result.media_type.value == data.media_type.value
            assert result.status == MediaStatus.pending
            assert result.year == data.year
            assert result.creator == data.creator
            assert result.notes == data.notes
            assert result.id is not None
            assert result.rating is None
            assert result.started_at is None
            assert result.completed_at is None

    asyncio.run(_run())


# -- Property 2 --------------------------------------------------------------


@settings(max_examples=100)
@given(bad_type=invalid_media_type_strings)
def test_rejection_of_invalid_media_type(bad_type):
    """For any string that is not a valid MediaType, creating a MediaCreate
    must raise a ValidationError."""
    with pytest.raises(ValidationError):
        MediaCreate(title="Test", media_type=bad_type)
