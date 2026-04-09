# Feature: social-login, Property 24: Feed muestra actividad de amigos ordenada cronológicamente
# Feature: social-login, Property 25: Feed limitado a 30 días
# Feature: social-login, Property 26: Acceso a colección de amigo
# Feature: social-login, Property 27: Rechazo de acceso a colección de no-amigo
"""Property tests for the social feed (Properties 24-27).

Validates: Requirements 9.1, 9.2, 9.3, 9.5, 10.1, 10.2
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

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
from backend.models.user import friendships
from backend.schemas.media import MediaFilters
from backend.services.feed_service import FeedService

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


async def _fresh_session():
    """Create a throwaway in-memory DB with users and yield a session.

    Users: alice (1), bob (2), carol (3).
    Alice and Bob are friends. Carol is not friends with anyone.
    """
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO users (id, email, username, password_hash) VALUES "
                "(1, 'alice@test.com', 'alice', 'fakehash'), "
                "(2, 'bob@test.com', 'bob', 'fakehash'), "
                "(3, 'carol@test.com', 'carol', 'fakehash')"
            )
        )
        # Alice <-> Bob friendship
        await conn.execute(
            sa.text(
                "INSERT INTO friendships (user_id, friend_id) VALUES "
                "(1, 2), (2, 1)"
            )
        )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()


def _make_item(
    user_id: int,
    title: str,
    media_type: str = "movie",
    status: str = "pending",
    rating: int | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> MediaItem:
    """Helper to build a MediaItem with explicit timestamps."""
    now = datetime.utcnow()
    return MediaItem(
        user_id=user_id,
        title=title,
        media_type=media_type,
        status=status,
        rating=rating,
        created_at=created_at or now,
        updated_at=updated_at or now,
        completed_at=completed_at,
    )


# -- Property 24: Feed shows friend activity ordered chronologically ----------


@settings(max_examples=100, deadline=None)
@given(
    num_items=st.integers(min_value=0, max_value=25),
    data=st.data(),
)
def test_feed_shows_friend_activity_ordered(num_items, data):
    """Feed contains only friend items, ordered desc by date, max 20 per page.

    **Validates: Requirements 9.1, 9.2, 9.3**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = FeedService()
            now = datetime.utcnow()

            # Create items for Bob (friend of Alice, user_id=2)
            for i in range(num_items):
                days_ago = data.draw(st.integers(min_value=0, max_value=25))
                item_date = now - timedelta(days=days_ago)
                item = _make_item(
                    user_id=2,
                    title=f"Bob Item {i}",
                    created_at=item_date,
                    updated_at=item_date,
                )
                sess.add(item)

            # Create items for Carol (NOT friend of Alice, user_id=3)
            for i in range(3):
                item = _make_item(
                    user_id=3,
                    title=f"Carol Item {i}",
                    created_at=now,
                    updated_at=now,
                )
                sess.add(item)

            await sess.commit()

            feed = await svc.get_feed(sess, user_id=1, page=1, size=20)

            # Only friend items (Bob's), never Carol's
            for entry in feed.items:
                assert entry.username == "bob"

            # Max 20 per page
            assert len(feed.items) <= 20

            # Ordered by date descending
            for i in range(len(feed.items) - 1):
                assert feed.items[i].date >= feed.items[i + 1].date

            # Each entry has required fields
            for entry in feed.items:
                assert entry.username
                assert entry.title
                assert entry.media_type
                assert entry.action in ("added", "completed", "rated")
                assert entry.date is not None

    asyncio.run(_run())


# -- Property 25: Feed limited to 30 days ------------------------------------


@settings(max_examples=100, deadline=None)
@given(
    old_days=st.integers(min_value=31, max_value=365),
    recent_days=st.integers(min_value=0, max_value=29),
)
def test_feed_limited_to_30_days(old_days, recent_days):
    """No feed entries older than 30 days.

    **Validates: Requirement 9.5**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = FeedService()
            now = datetime.utcnow()

            # Old item (should NOT appear)
            old_date = now - timedelta(days=old_days)
            old_item = _make_item(
                user_id=2,
                title="Old Item",
                created_at=old_date,
                updated_at=old_date,
            )
            sess.add(old_item)

            # Recent item (should appear)
            recent_date = now - timedelta(days=recent_days)
            recent_item = _make_item(
                user_id=2,
                title="Recent Item",
                created_at=recent_date,
                updated_at=recent_date,
            )
            sess.add(recent_item)

            await sess.commit()

            cutoff = now - timedelta(days=30)
            feed = await svc.get_feed(sess, user_id=1, page=1, size=20)

            # No entries older than 30 days
            for entry in feed.items:
                assert entry.date >= cutoff

            # The recent item should be present
            titles = [e.title for e in feed.items]
            assert "Recent Item" in titles
            assert "Old Item" not in titles

    asyncio.run(_run())


# -- Property 26: Friend collection access ------------------------------------


@settings(max_examples=100, deadline=None)
@given(
    num_items=st.integers(min_value=1, max_value=10),
    use_filter=st.sampled_from(["none", "media_type", "status", "search"]),
)
def test_friend_collection_access(num_items, use_filter):
    """Friends can see each other's collection with filters, results only from friend.

    **Validates: Requirement 10.1**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = FeedService()
            now = datetime.utcnow()

            types = ["movie", "book", "series"]
            statuses = ["pending", "in_progress", "completed"]

            # Create items for Bob (friend of Alice)
            for i in range(num_items):
                item = _make_item(
                    user_id=2,
                    title=f"Bob Title {i}",
                    media_type=types[i % 3],
                    status=statuses[i % 3],
                    created_at=now,
                    updated_at=now,
                )
                sess.add(item)

            # Create items for Carol (NOT friend of Alice)
            carol_item = _make_item(
                user_id=3,
                title="Carol Title 0",
                created_at=now,
                updated_at=now,
            )
            sess.add(carol_item)

            await sess.commit()

            # Build filters
            filters = MediaFilters()
            if use_filter == "media_type":
                from backend.schemas.media import MediaType
                filters = MediaFilters(media_type=MediaType.movie)
            elif use_filter == "status":
                from backend.schemas.media import MediaStatus
                filters = MediaFilters(status=MediaStatus.pending)
            elif use_filter == "search":
                filters = MediaFilters(search="Bob")

            # Alice views Bob's collection
            result = await svc.get_friend_collection(
                sess, user_id=1, friend_id=2, filters=filters, page=1, size=20
            )

            # All items belong to Bob
            for item in result.items:
                assert "Carol" not in item.title

            # Pagination metadata is consistent
            assert result.page == 1
            assert result.total >= 0
            assert result.pages >= 0

            # If filtering by media_type=movie, all results are movies
            if use_filter == "media_type":
                for item in result.items:
                    assert item.media_type == "movie"
            elif use_filter == "status":
                for item in result.items:
                    assert item.status == "pending"
            elif use_filter == "search":
                for item in result.items:
                    assert "bob" in item.title.lower()

    asyncio.run(_run())


# -- Property 27: Non-friend collection rejection ----------------------------


@settings(max_examples=100, deadline=None)
@given(
    viewer_id=st.sampled_from([1, 3]),
    target_id=st.sampled_from([2, 3]),
)
def test_non_friend_collection_rejection(viewer_id, target_id):
    """Non-friends get 403 when trying to view collection.

    **Validates: Requirement 10.2**
    """
    from fastapi import HTTPException

    async def _run():
        async for sess in _fresh_session():
            svc = FeedService()

            # Check if they are actually friends
            row = await sess.execute(
                sa.select(friendships).where(
                    friendships.c.user_id == viewer_id,
                    friendships.c.friend_id == target_id,
                )
            )
            are_friends = row.first() is not None

            if are_friends:
                # Should succeed — skip this combo
                return

            # Not friends → should get 403
            with pytest.raises(HTTPException) as exc_info:
                await svc.get_friend_collection(
                    sess,
                    user_id=viewer_id,
                    friend_id=target_id,
                    filters=MediaFilters(),
                    page=1,
                    size=20,
                )
            assert exc_info.value.status_code == 403

    asyncio.run(_run())
