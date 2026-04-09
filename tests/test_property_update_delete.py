# Feature: media-tracker, Property 4: Update preserves modified fields
# Feature: media-tracker, Property 5: Deletion removes the item
"""Property tests for update and deletion (Properties 4, 5).

Validates: Requirements 4.1, 4.3, 5.2
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

import sqlalchemy as sa

from backend.models.media import Base
from backend.models.user import User  # noqa: F401 — registers users table
from backend.schemas.media import (
    MediaCreate,
    MediaType,
    MediaUpdate,
)
from backend.services.media_service import MediaService

# -- Hypothesis strategies ---------------------------------------------------

valid_media_types = st.sampled_from(
    [MediaType.movie, MediaType.book, MediaType.series]
)

valid_media_create = st.builds(
    MediaCreate,
    title=st.text(min_size=1, max_size=60).filter(lambda t: t.strip()),
    media_type=valid_media_types,
    year=st.one_of(st.none(), st.integers(min_value=1800, max_value=2100)),
    creator=st.one_of(st.none(), st.text(min_size=1, max_size=60)),
    notes=st.one_of(st.none(), st.text(max_size=100)),
    tags=st.just([]),
)

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@st.composite
def media_update_strategy(draw):
    """Build a MediaUpdate with only a random subset of fields set,
    so that exclude_unset works correctly."""
    kwargs = {}
    if draw(st.booleans()):
        kwargs["title"] = draw(
            st.text(min_size=1, max_size=60).filter(lambda t: t.strip())
        )
    if draw(st.booleans()):
        kwargs["media_type"] = draw(valid_media_types)
    if draw(st.booleans()):
        kwargs["year"] = draw(
            st.one_of(st.none(), st.integers(min_value=1800, max_value=2100))
        )
    if draw(st.booleans()):
        kwargs["creator"] = draw(
            st.one_of(st.none(), st.text(min_size=1, max_size=60))
        )
    if draw(st.booleans()):
        kwargs["notes"] = draw(st.one_of(st.none(), st.text(max_size=100)))
    return MediaUpdate(**kwargs)


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


# -- Property 4 --------------------------------------------------------------


@settings(max_examples=100, deadline=None)
@given(create_data=valid_media_create, update_data=media_update_strategy())
def test_update_preserves_modified_fields(create_data, update_data):
    """For any existing item and any valid update, the result must reflect
    exactly the modified fields while keeping unchanged fields intact."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data, user_id=1)

            updated = await svc.update(sess, created.id, update_data, user_id=1)
            update_dict = update_data.model_dump(exclude_unset=True)

            # Modified fields should reflect the update
            for field, value in update_dict.items():
                actual = getattr(updated, field)
                if field == "media_type" and value is not None:
                    assert actual.value == value.value
                else:
                    assert actual == value

            # Unmodified fields should remain the same
            if "title" not in update_dict:
                assert updated.title == created.title
            if "media_type" not in update_dict:
                assert updated.media_type == created.media_type
            if "year" not in update_dict:
                assert updated.year == created.year
            if "creator" not in update_dict:
                assert updated.creator == created.creator
            if "notes" not in update_dict:
                assert updated.notes == created.notes

            # Status and rating should never change via update
            assert updated.status == created.status
            assert updated.rating == created.rating

    asyncio.run(_run())


# -- Property 5 --------------------------------------------------------------


@settings(max_examples=100, deadline=None)
@given(create_data=valid_media_create)
def test_deletion_removes_the_item(create_data):
    """For any existing item, deletion must succeed and the item must no
    longer be retrievable."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data, user_id=1)

            await svc.delete(sess, created.id, user_id=1)

            with pytest.raises(HTTPException) as exc_info:
                await svc.get(sess, created.id, user_id=1)
            assert exc_info.value.status_code == 404

    asyncio.run(_run())
