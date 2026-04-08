# Feature: media-tracker, Property 6: Status transition automatically records dates
# Feature: media-tracker, Property 7: Rejection of invalid status
# Feature: media-tracker, Property 8: Rating within valid range
# Feature: media-tracker, Property 9: Tags with limit of 10
"""Property tests for status, rating, and tags (Properties 6, 7, 8, 9).

Validates: Requirements 6.1, 6.2, 6.3, 7.1, 7.2, 8.1, 8.3, 8.4
"""

import asyncio

import pytest
from fastapi import HTTPException
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.models.media import Base
from backend.schemas.media import (
    MediaCreate,
    MediaStatus,
    MediaType,
)
from backend.services.media_service import MediaService

# -- Shared helpers ----------------------------------------------------------

valid_media_types = st.sampled_from(
    [MediaType.movie, MediaType.book, MediaType.series]
)

simple_media_create = st.builds(
    MediaCreate,
    title=st.text(min_size=1, max_size=60).filter(lambda t: t.strip()),
    media_type=valid_media_types,
    year=st.none(),
    creator=st.none(),
    notes=st.none(),
    tags=st.just([]),
)

valid_status_values = st.sampled_from(["pending", "in_progress", "completed"])

invalid_status_strings = st.text(min_size=1, max_size=50).filter(
    lambda s: s not in {"pending", "in_progress", "completed"}
)

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


async def _fresh_session():
    """Create a throwaway in-memory DB and yield a session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()


# -- Property 6 --------------------------------------------------------------


@settings(max_examples=100, deadline=None)
@given(create_data=simple_media_create)
def test_status_transition_records_started_at(create_data):
    """When changing status to 'in_progress', started_at must be set
    automatically if it was not already set."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data)
            assert created.started_at is None

            updated = await svc.update_status(sess, created.id, "in_progress")
            assert updated.started_at is not None
            assert updated.status == MediaStatus.in_progress

            # Setting in_progress again should NOT overwrite started_at
            first_started = updated.started_at
            updated2 = await svc.update_status(sess, updated.id, "in_progress")
            assert updated2.started_at == first_started

    asyncio.run(_run())


@settings(max_examples=100, deadline=None)
@given(create_data=simple_media_create)
def test_status_transition_records_completed_at(create_data):
    """When changing status to 'completed', completed_at must be set
    automatically."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data)
            assert created.completed_at is None

            updated = await svc.update_status(sess, created.id, "completed")
            assert updated.completed_at is not None
            assert updated.status == MediaStatus.completed

    asyncio.run(_run())


# -- Property 7 --------------------------------------------------------------


@settings(max_examples=100)
@given(bad_status=invalid_status_strings, create_data=simple_media_create)
def test_rejection_of_invalid_status(bad_status, create_data):
    """For any string that is not a valid status, update_status must
    raise a 400 error."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data)

            with pytest.raises(HTTPException) as exc_info:
                await svc.update_status(sess, created.id, bad_status)
            assert exc_info.value.status_code == 400

    asyncio.run(_run())


# -- Property 8 --------------------------------------------------------------


@settings(max_examples=100, deadline=None)
@given(
    create_data=simple_media_create,
    rating=st.integers(min_value=1, max_value=10),
)
def test_valid_rating_accepted(create_data, rating):
    """For any integer between 1 and 10, the rating must be accepted
    and saved."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data)

            updated = await svc.update_rating(sess, created.id, rating)
            assert updated.rating == rating

    asyncio.run(_run())


@settings(max_examples=100, deadline=None)
@given(
    create_data=simple_media_create,
    bad_rating=st.integers().filter(lambda r: r < 1 or r > 10),
)
def test_invalid_rating_rejected(create_data, bad_rating):
    """For any number outside 1-10, update_rating must raise a 400 error."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data)

            with pytest.raises(HTTPException) as exc_info:
                await svc.update_rating(sess, created.id, bad_rating)
            assert exc_info.value.status_code == 400

    asyncio.run(_run())


# -- Property 9 --------------------------------------------------------------


@settings(max_examples=100, deadline=None)
@given(
    create_data=simple_media_create,
    tags=st.lists(
        st.text(min_size=1, max_size=30), min_size=0, max_size=10, unique=True
    ),
)
def test_tags_within_limit_accepted(create_data, tags):
    """For any list of up to 10 tags, they must be saved correctly."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data)

            updated = await svc.update_tags(sess, created.id, tags)
            assert set(updated.tags) == set(tags)
            assert len(updated.tags) <= 10

    asyncio.run(_run())


@settings(max_examples=100, deadline=None)
@given(
    create_data=simple_media_create,
    tags=st.lists(
        st.text(min_size=1, max_size=30), min_size=11, max_size=15, unique=True
    ),
)
def test_tags_over_limit_rejected(create_data, tags):
    """For any list of more than 10 tags, update_tags must raise a 400 error."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data)

            with pytest.raises(HTTPException) as exc_info:
                await svc.update_tags(sess, created.id, tags)
            assert exc_info.value.status_code == 400

    asyncio.run(_run())
