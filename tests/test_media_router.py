"""Unit tests for the media CRUD router endpoints."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.main import app
from backend.db import get_session
from backend.models.media import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Create a fresh async engine for each test."""
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Yield a fresh async session backed by in-memory SQLite."""
    factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as sess:
        yield sess


@pytest_asyncio.fixture
async def client(engine):
    """Provide an async HTTP client wired to the FastAPI app with test DB."""
    factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False,
    )

    async def _override_session():
        async with factory() as sess:
            yield sess

    app.dependency_overrides[get_session] = _override_session

    # Register the router (idempotent — FastAPI deduplicates)
    from backend.routers.media import router
    if router not in app.router.routes:
        app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── POST /api/media ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_media_returns_201(client):
    """Creating a valid media item returns 201 with correct data."""
    payload = {"title": "Inception", "media_type": "movie"}
    resp = await client.post("/api/media", json=payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Inception"
    assert body["media_type"] == "movie"
    assert body["status"] == "pending"
    assert body["id"] is not None


@pytest.mark.asyncio
async def test_create_media_missing_title_returns_422(client):
    """Missing title triggers a validation error."""
    resp = await client.post("/api/media", json={"media_type": "book"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_media_invalid_type_returns_422(client):
    """Invalid media_type triggers a validation error."""
    resp = await client.post(
        "/api/media", json={"title": "Test", "media_type": "podcast"},
    )
    assert resp.status_code == 422


# ── GET /api/media ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_media_empty(client):
    """Listing an empty catalog returns an empty page."""
    resp = await client.get("/api/media")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_list_media_with_items(client):
    """Listing after creation returns the created items."""
    await client.post("/api/media", json={"title": "A", "media_type": "movie"})
    await client.post("/api/media", json={"title": "B", "media_type": "book"})

    resp = await client.get("/api/media")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_list_media_filter_by_type(client):
    """Filtering by media_type returns only matching items."""
    await client.post("/api/media", json={"title": "A", "media_type": "movie"})
    await client.post("/api/media", json={"title": "B", "media_type": "book"})

    resp = await client.get("/api/media", params={"media_type": "book"})
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["media_type"] == "book"


# ── GET /api/media/{id} ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_media_by_id(client):
    """Fetching an existing item by ID returns 200."""
    create_resp = await client.post(
        "/api/media", json={"title": "Dune", "media_type": "book"},
    )
    media_id = create_resp.json()["id"]

    resp = await client.get(f"/api/media/{media_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Dune"


@pytest.mark.asyncio
async def test_get_media_not_found(client):
    """Fetching a non-existent ID returns 404."""
    resp = await client.get("/api/media/9999")
    assert resp.status_code == 404


# ── PUT /api/media/{id} ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_media(client):
    """Updating fields returns the modified item."""
    create_resp = await client.post(
        "/api/media", json={"title": "Old Title", "media_type": "movie"},
    )
    media_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/media/{media_id}", json={"title": "New Title"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_update_media_not_found(client):
    """Updating a non-existent item returns 404."""
    resp = await client.put(
        "/api/media/9999", json={"title": "Nope"},
    )
    assert resp.status_code == 404


# ── DELETE /api/media/{id} ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_media(client):
    """Deleting an existing item returns 204 and item is gone."""
    create_resp = await client.post(
        "/api/media", json={"title": "Temp", "media_type": "series"},
    )
    media_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/media/{media_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/media/{media_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_media_not_found(client):
    """Deleting a non-existent item returns 404."""
    resp = await client.delete("/api/media/9999")
    assert resp.status_code == 404


# ── PATCH /api/media/{id}/status ─────────────────────────────────────


@pytest.mark.asyncio
async def test_update_status_to_in_progress(client):
    """Changing status to in_progress returns 200 with started_at set."""
    create_resp = await client.post(
        "/api/media", json={"title": "Matrix", "media_type": "movie"},
    )
    media_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/media/{media_id}/status", json={"status": "in_progress"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "in_progress"
    assert body["started_at"] is not None


@pytest.mark.asyncio
async def test_update_status_to_completed(client):
    """Changing status to completed returns 200 with completed_at set."""
    create_resp = await client.post(
        "/api/media", json={"title": "Dune", "media_type": "book"},
    )
    media_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/media/{media_id}/status", json={"status": "completed"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["completed_at"] is not None


@pytest.mark.asyncio
async def test_update_status_invalid(client):
    """Invalid status value returns 400."""
    create_resp = await client.post(
        "/api/media", json={"title": "Test", "media_type": "movie"},
    )
    media_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/media/{media_id}/status", json={"status": "unknown"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_status_not_found(client):
    """Updating status of a non-existent item returns 404."""
    resp = await client.patch(
        "/api/media/9999/status", json={"status": "pending"},
    )
    assert resp.status_code == 404


# ── PATCH /api/media/{id}/rating ─────────────────────────────────────


@pytest.mark.asyncio
async def test_update_rating_valid(client):
    """Assigning a valid rating returns 200 with the rating saved."""
    create_resp = await client.post(
        "/api/media", json={"title": "Interstellar", "media_type": "movie"},
    )
    media_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/media/{media_id}/rating", json={"rating": 8},
    )
    assert resp.status_code == 200
    assert resp.json()["rating"] == 8


@pytest.mark.asyncio
async def test_update_rating_out_of_range(client):
    """Rating outside 1-10 returns 400."""
    create_resp = await client.post(
        "/api/media", json={"title": "Test", "media_type": "book"},
    )
    media_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/media/{media_id}/rating", json={"rating": 0},
    )
    assert resp.status_code == 400

    resp = await client.patch(
        f"/api/media/{media_id}/rating", json={"rating": 11},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_rating_not_found(client):
    """Rating a non-existent item returns 404."""
    resp = await client.patch(
        "/api/media/9999/rating", json={"rating": 5},
    )
    assert resp.status_code == 404


# ── PUT /api/media/{id}/tags ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_tags_valid(client):
    """Assigning tags returns 200 with the tags saved."""
    create_resp = await client.post(
        "/api/media", json={"title": "1984", "media_type": "book"},
    )
    media_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/media/{media_id}/tags",
        json={"tags": ["dystopia", "classic"]},
    )
    assert resp.status_code == 200
    assert set(resp.json()["tags"]) == {"dystopia", "classic"}


@pytest.mark.asyncio
async def test_update_tags_over_limit(client):
    """More than 10 tags returns 400."""
    create_resp = await client.post(
        "/api/media", json={"title": "Test", "media_type": "series"},
    )
    media_id = create_resp.json()["id"]

    tags = [f"tag{i}" for i in range(11)]
    resp = await client.put(
        f"/api/media/{media_id}/tags", json={"tags": tags},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_tags_not_found(client):
    """Tagging a non-existent item returns 404."""
    resp = await client.put(
        "/api/media/9999/tags", json={"tags": ["test"]},
    )
    assert resp.status_code == 404
