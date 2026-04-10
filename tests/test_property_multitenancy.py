# Feature: social-login, Property 11: user_id assignment on create
# Feature: social-login, Property 12: listing isolation by user
# Feature: social-login, Property 13: cross-access rejection between users
# Feature: social-login, Property 14: stats isolation
"""Property tests for multi-tenancy isolation (Properties 11-14).

Validates: Requirements 5.1, 5.2, 5.3, 5.5
"""
from __future__ import annotations

import asyncio

import pytest
import sqlalchemy as sa
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.models.media import Base, MediaItem
from backend.models.user import User  # noqa: F401
from backend.schemas.media import MediaCreate, MediaFilters, MediaType, MediaUpdate
from backend.services.media_service import MediaService
from backend.services.stats_service import StatsService

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
user_id_strategy = st.sampled_from([1, 2])
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


async def _fresh_session():
    """Create a throwaway in-memory DB with two test users and yield a session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO users (id, email, username, password_hash) "
                "VALUES (1, 'alice@test.com', 'alice', 'fakehash'), "
                "(2, 'bob@test.com', 'bob', 'fakehash')"
            )
        )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()


# -- Property 11: user_id assignment on create --------------------------------


@settings(max_examples=100, deadline=None)
@given(data=valid_media_create, uid=user_id_strategy)
def test_user_id_assignment_on_create(data, uid):
    """For any valid MediaCreate and user_id, the created item must belong
    to the specified user.

    **Validates: Requirement 5.1**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            result = await svc.create(sess, data, user_id=uid)

            assert result.id is not None

            # Verify directly in DB
            item = await sess.get(MediaItem, result.id)
            assert item is not None
            assert item.user_id == uid

    asyncio.run(_run())


# -- Property 12: listing isolation by user -----------------------------------


@settings(max_examples=100, deadline=None)
@given(
    items_a=st.lists(valid_media_create, min_size=0, max_size=5),
    items_b=st.lists(valid_media_create, min_size=0, max_size=5),
)
def test_listing_isolation_by_user(items_a, items_b):
    """For any two users with their own items, listing returns only
    items belonging to the queried user.

    **Validates: Requirement 5.2**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()

            ids_a = []
            for item_data in items_a:
                r = await svc.create(sess, item_data, user_id=1)
                ids_a.append(r.id)

            ids_b = []
            for item_data in items_b:
                r = await svc.create(sess, item_data, user_id=2)
                ids_b.append(r.id)

            # List for user 1
            result_a = await svc.list(sess, MediaFilters(), user_id=1)
            listed_ids_a = {i.id for i in result_a.items}
            assert listed_ids_a == set(ids_a)

            # List for user 2
            result_b = await svc.list(sess, MediaFilters(), user_id=2)
            listed_ids_b = {i.id for i in result_b.items}
            assert listed_ids_b == set(ids_b)

    asyncio.run(_run())


# -- Property 13: cross-access rejection -------------------------------------


@settings(max_examples=100, deadline=None)
@given(data=valid_media_create)
def test_cross_access_rejection(data):
    """User B cannot access, modify, or delete items owned by user A.

    **Validates: Requirement 5.3**
    """
    from fastapi import HTTPException

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, data, user_id=1)
            item_id = created.id

            # User 2 tries to get
            with pytest.raises(HTTPException) as exc_info:
                await svc.get(sess, item_id, user_id=2)
            assert exc_info.value.status_code == 403

            # User 2 tries to update
            with pytest.raises(HTTPException) as exc_info:
                await svc.update(sess, item_id, MediaUpdate(title="hacked"), user_id=2)
            assert exc_info.value.status_code == 403

            # User 2 tries to delete
            with pytest.raises(HTTPException) as exc_info:
                await svc.delete(sess, item_id, user_id=2)
            assert exc_info.value.status_code == 403

    asyncio.run(_run())


# -- Property 14: stats and export isolation ----------------------------------


@settings(max_examples=100, deadline=None)
@given(
    items_a=st.lists(valid_media_create, min_size=1, max_size=5),
    items_b=st.lists(valid_media_create, min_size=1, max_size=5),
)
def test_stats_and_export_isolation(items_a, items_b):
    """Stats for each user reflect only their own items.

    **Validates: Requirement 5.5**
    """

    async def _run():
        async for sess in _fresh_session():
            media_svc = MediaService()
            stats_svc = StatsService()

            for item_data in items_a:
                await media_svc.create(sess, item_data, user_id=1)
            for item_data in items_b:
                await media_svc.create(sess, item_data, user_id=2)

            # Stats isolation
            stats_a = await stats_svc.get_stats(sess, user_id=1)
            total_a = sum(stats_a.by_type.values())
            assert total_a == len(items_a)

            stats_b = await stats_svc.get_stats(sess, user_id=2)
            total_b = sum(stats_b.by_type.values())
            assert total_b == len(items_b)

    asyncio.run(_run())
