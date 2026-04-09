# Feature: backend-datetime-image-fix, Property 2: Preservation — Comportamiento existente sin cambios
"""Preservation property tests — baseline behavior that must not change after the fix.

These tests MUST PASS on unfixed code. They capture the existing correct behavior
for operations NOT affected by the datetime/image bugs:
- Item creation (timestamps via server_default)
- Item retrieval (GET)
- Item deletion (DELETE)
- _to_response() image_url construction

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import sqlalchemy as sa

from backend.models.media import Base, MediaItem
from backend.models.user import User  # noqa: F401 — registers users table
from backend.schemas.media import MediaCreate, MediaType
from backend.services.media_service import MediaService, _to_response

# -- Strategies --------------------------------------------------------------

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

image_path_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_./"),
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip() and not s.startswith("/"))

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


# -- Preservation Test 1: create() returns non-null naive timestamps ---------


@settings(max_examples=10, deadline=None)
@given(create_data=simple_media_create)
def test_create_returns_nonnull_naive_timestamps(create_data):
    """For any valid MediaCreate, create() returns an item with non-null
    created_at and updated_at, both naive datetimes.

    **Validates: Requirements 3.1, 3.2**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            result = await svc.create(sess, create_data, user_id=1)

            assert result.created_at is not None, (
                "created_at must not be None after create()"
            )
            assert result.updated_at is not None, (
                "updated_at must not be None after create()"
            )
            assert isinstance(result.created_at, datetime), (
                f"created_at must be a datetime, got {type(result.created_at)}"
            )
            assert isinstance(result.updated_at, datetime), (
                f"updated_at must be a datetime, got {type(result.updated_at)}"
            )
            # Both must be naive (no tzinfo) — server_default=func.now() produces naive
            assert result.created_at.tzinfo is None, (
                f"created_at has tzinfo={result.created_at.tzinfo!r}, expected None (naive)"
            )
            assert result.updated_at.tzinfo is None, (
                f"updated_at has tzinfo={result.updated_at.tzinfo!r}, expected None (naive)"
            )

    asyncio.run(_run())


# -- Preservation Test 2: get() returns same item with correct timestamps ----


@settings(max_examples=10, deadline=None)
@given(create_data=simple_media_create)
def test_get_returns_item_with_correct_timestamps(create_data):
    """For any created item, get() returns the same item with correct timestamps.

    **Validates: Requirements 3.2, 3.3**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data, user_id=1)

            fetched = await svc.get(sess, created.id, user_id=1)

            assert fetched.id == created.id, (
                f"get() returned id={fetched.id}, expected {created.id}"
            )
            assert fetched.title == created.title, (
                f"get() returned title={fetched.title!r}, expected {created.title!r}"
            )
            assert fetched.created_at == created.created_at, (
                f"get() created_at={fetched.created_at!r} != create() created_at={created.created_at!r}"
            )
            assert fetched.updated_at == created.updated_at, (
                f"get() updated_at={fetched.updated_at!r} != create() updated_at={created.updated_at!r}"
            )
            assert fetched.created_at.tzinfo is None, (
                f"get() created_at has tzinfo={fetched.created_at.tzinfo!r}, expected None"
            )
            assert fetched.updated_at.tzinfo is None, (
                f"get() updated_at has tzinfo={fetched.updated_at.tzinfo!r}, expected None"
            )

    asyncio.run(_run())


# -- Preservation Test 3: delete() completes without error -------------------


@settings(max_examples=10, deadline=None)
@given(create_data=simple_media_create)
def test_delete_completes_without_error(create_data):
    """For any created item, delete() completes without error.

    **Validates: Requirements 3.3**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data, user_id=1)

            # delete() should not raise
            await svc.delete(sess, created.id, user_id=1)

    asyncio.run(_run())


# -- Preservation Test 4: _to_response() builds image_url correctly ----------


@settings(max_examples=10, deadline=None)
@given(
    create_data=simple_media_create,
    img_path=image_path_strategy,
)
def test_to_response_builds_image_url(create_data, img_path):
    """For any item with image_path set, _to_response() builds
    image_url as /images/<image_path>.

    **Validates: Requirements 3.4, 3.5, 3.6, 3.7**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data, user_id=1)

            # Manually set image_path on the ORM object
            item = await sess.get(MediaItem, created.id)
            item.image_path = img_path
            await sess.commit()
            await sess.refresh(item)

            response = _to_response(item)

            expected_url = f"/images/{img_path}"
            assert response.image_url == expected_url, (
                f"image_url={response.image_url!r}, expected {expected_url!r}"
            )

    asyncio.run(_run())
