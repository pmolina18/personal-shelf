"""Unit tests for the feed router endpoints.

Tests: feed with friends, empty feed, pagination, friend collection
with filters, non-friend access (403).

Uses httpx.AsyncClient + ASGITransport with app.dependency_overrides.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.db import get_session
from backend.dependencies import get_current_user
from backend.main import app
from backend.models.media import Base, MediaItem, Tag
from backend.models.user import User, friendships

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# Mutable container so the override can be switched mid-test
_current_user_id: dict[str, int] = {"uid": 1}


@pytest_asyncio.fixture
async def setup():
    """Create a fresh in-memory DB with users, friendships, and media items."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    now = datetime.utcnow()

    async with factory() as sess:
        # Seed users
        for uid, email, uname in [
            (1, "alice@test.com", "alice"),
            (2, "bob@test.com", "bob"),
            (3, "carol@test.com", "carol"),
        ]:
            sess.add(User(id=uid, email=email, username=uname, password_hash="fakehash"))
        await sess.flush()

        # Alice <-> Bob friendship
        await sess.execute(
            insert(friendships).values(user_id=1, friend_id=2)
        )
        await sess.execute(
            insert(friendships).values(user_id=2, friend_id=1)
        )

        # Bob's media items (recent — should appear in Alice's feed)
        for i in range(5):
            sess.add(
                MediaItem(
                    user_id=2,
                    title=f"Bob Movie {i}",
                    media_type="movie",
                    status="pending",
                    created_at=now - timedelta(days=i),
                    updated_at=now - timedelta(days=i),
                )
            )

        # Bob's old item (>30 days — should NOT appear)
        sess.add(
            MediaItem(
                user_id=2,
                title="Bob Old Movie",
                media_type="movie",
                status="pending",
                created_at=now - timedelta(days=45),
                updated_at=now - timedelta(days=45),
            )
        )

        # Bob's completed item
        sess.add(
            MediaItem(
                user_id=2,
                title="Bob Completed Book",
                media_type="book",
                status="completed",
                created_at=now - timedelta(days=10),
                updated_at=now - timedelta(days=2),
                completed_at=now - timedelta(days=2),
            )
        )

        # Bob's rated item
        sess.add(
            MediaItem(
                user_id=2,
                title="Bob Rated Series",
                media_type="series",
                status="completed",
                rating=8,
                created_at=now - timedelta(days=15),
                updated_at=now - timedelta(days=1),
                completed_at=now - timedelta(days=5),
            )
        )

        # Carol's items (NOT friend of Alice — should NOT appear in feed)
        sess.add(
            MediaItem(
                user_id=3,
                title="Carol Movie",
                media_type="movie",
                status="pending",
                created_at=now,
                updated_at=now,
            )
        )

        # Tag for Bob's first item
        tag = Tag(name="action")
        sess.add(tag)
        await sess.flush()
        bob_item_result = await sess.get(MediaItem, 1)
        if bob_item_result:
            bob_item_result.tags = [tag]

        await sess.commit()

    async def _session_override():
        async with factory() as sess:
            yield sess

    async def _user_override():
        async with factory() as sess:
            user = await sess.get(User, _current_user_id["uid"])
            return user

    app.dependency_overrides[get_session] = _session_override
    app.dependency_overrides[get_current_user] = _user_override

    yield factory

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(setup):
    """Yield an httpx AsyncClient wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def as_user(uid: int):
    """Switch the current authenticated user for subsequent requests."""
    _current_user_id["uid"] = uid


# -- Feed tests ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_feed_with_friends(client):
    """GET /api/feed returns friend activity entries."""
    as_user(1)
    resp = await client.get("/api/feed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0
    # All entries are from Bob (Alice's friend)
    for entry in data["items"]:
        assert entry["username"] == "bob"
        assert entry["action"] in ("added", "completed", "rated")
        assert entry["title"]
        assert entry["media_type"]
        assert entry["date"]


@pytest.mark.asyncio
async def test_feed_empty(client):
    """GET /api/feed for user with no friends returns empty feed."""
    as_user(3)  # Carol has no friends
    resp = await client.get("/api/feed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_feed_excludes_old_items(client):
    """GET /api/feed does not include items older than 30 days."""
    as_user(1)
    resp = await client.get("/api/feed")
    assert resp.status_code == 200
    data = resp.json()
    titles = [e["title"] for e in data["items"]]
    assert "Bob Old Movie" not in titles


@pytest.mark.asyncio
async def test_feed_ordered_desc(client):
    """GET /api/feed returns entries ordered by date descending."""
    as_user(1)
    resp = await client.get("/api/feed")
    assert resp.status_code == 200
    data = resp.json()
    dates = [e["date"] for e in data["items"]]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.asyncio
async def test_feed_pagination(client):
    """GET /api/feed?page=1&size=3 returns at most 3 items with correct metadata."""
    as_user(1)
    resp = await client.get("/api/feed", params={"page": 1, "size": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 3
    assert data["page"] == 1
    assert data["size"] == 3
    assert data["pages"] >= 1


# -- Friend collection tests --------------------------------------------------


@pytest.mark.asyncio
async def test_friend_collection_success(client):
    """GET /api/feed/friends/{id}/collection returns friend's items."""
    as_user(1)
    resp = await client.get("/api/feed/friends/2/collection")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_friend_collection_filter_media_type(client):
    """GET /api/feed/friends/{id}/collection?media_type=book filters correctly."""
    as_user(1)
    resp = await client.get(
        "/api/feed/friends/2/collection", params={"media_type": "book"}
    )
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["media_type"] == "book"


@pytest.mark.asyncio
async def test_friend_collection_filter_status(client):
    """GET /api/feed/friends/{id}/collection?status=completed filters correctly."""
    as_user(1)
    resp = await client.get(
        "/api/feed/friends/2/collection", params={"status": "completed"}
    )
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["status"] == "completed"


@pytest.mark.asyncio
async def test_friend_collection_filter_search(client):
    """GET /api/feed/friends/{id}/collection?search=Rated filters by title."""
    as_user(1)
    resp = await client.get(
        "/api/feed/friends/2/collection", params={"search": "Rated"}
    )
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert "rated" in item["title"].lower()


@pytest.mark.asyncio
async def test_friend_collection_filter_tag(client):
    """GET /api/feed/friends/{id}/collection?tag=action filters by tag."""
    as_user(1)
    resp = await client.get(
        "/api/feed/friends/2/collection", params={"tag": "action"}
    )
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert "action" in item["tags"]


@pytest.mark.asyncio
async def test_friend_collection_non_friend_403(client):
    """GET /api/feed/friends/{id}/collection for non-friend returns 403."""
    as_user(1)  # Alice is NOT friends with Carol
    resp = await client.get("/api/feed/friends/3/collection")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_friend_collection_non_friend_reverse_403(client):
    """GET /api/feed/friends/{id}/collection — Carol can't see Alice's collection."""
    as_user(3)  # Carol is NOT friends with Alice
    resp = await client.get("/api/feed/friends/1/collection")
    assert resp.status_code == 403
