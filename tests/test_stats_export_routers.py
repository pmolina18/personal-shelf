"""Unit tests for stats, export/import, and image router endpoints."""

import pytest
import pytest_asyncio
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


from backend.db import get_session
from backend.dependencies import get_current_user
from backend.main import app
from backend.models.media import Base
from backend.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Create a fresh async engine for each test."""
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
async def client(engine):
    """Provide an async HTTP client wired to the FastAPI app with test DB."""
    factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False,
    )

    async def _override_session():
        async with factory() as sess:
            yield sess

    app.dependency_overrides[get_session] = _override_session

    async def _override_user():
        return User(id=1, email="test@test.com", username="testuser", password_hash="fakehash")

    app.dependency_overrides[get_current_user] = _override_user

    # Register routers (idempotent — FastAPI deduplicates)
    from backend.routers.export_import import router as export_router
    from backend.routers.media import router as media_router
    from backend.routers.stats import router as stats_router

    for r in (media_router, stats_router, export_router):
        if r not in app.router.routes:
            app.include_router(r)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── GET /api/stats ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stats_empty_catalog(client):
    """Stats on an empty catalog return zero counts."""
    resp = await client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["by_type"] == {"movie": 0, "book": 0, "series": 0}
    assert body["by_status"] == {"pending": 0, "in_progress": 0, "completed": 0}


@pytest.mark.asyncio
async def test_stats_with_items(client):
    """Stats reflect created items."""
    await client.post("/api/media", json={"title": "A", "media_type": "movie"})
    await client.post("/api/media", json={"title": "B", "media_type": "book"})

    resp = await client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["by_type"]["movie"] == 1
    assert body["by_type"]["book"] == 1
    assert body["by_status"]["pending"] == 2


# ── GET /api/export ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_export_empty_catalog(client):
    """Exporting an empty catalog returns version and empty items."""
    resp = await client.get("/api/export")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1.0"
    assert body["items"] == []


@pytest.mark.asyncio
async def test_export_includes_items(client):
    """Exported JSON contains all created items."""
    await client.post("/api/media", json={"title": "X", "media_type": "movie"})
    await client.post("/api/media", json={"title": "Y", "media_type": "series"})

    resp = await client.get("/api/export")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2


# ── POST /api/import ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_import_round_trip(client):
    """Exporting then importing recreates items."""
    await client.post("/api/media", json={"title": "RT", "media_type": "book"})

    export_resp = await client.get("/api/export")
    export_data = export_resp.json()

    # Delete the original
    items_resp = await client.get("/api/media")
    for item in items_resp.json()["items"]:
        await client.delete(f"/api/media/{item['id']}")

    # Import
    import_resp = await client.post("/api/import", json=export_data)
    assert import_resp.status_code == 200
    body = import_resp.json()
    assert body["created"] == 1
    assert body["errors"] == []


@pytest.mark.asyncio
async def test_import_invalid_format(client):
    """Importing malformed JSON returns 400."""
    resp = await client.post("/api/import", json={"bad": "data"})
    assert resp.status_code == 400


# ── GET /api/media/{id}/image ────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_image_returns_url(client):
    """Image endpoint returns the image_url for an existing item."""
    create_resp = await client.post(
        "/api/media", json={"title": "Img Test", "media_type": "movie"},
    )
    media_id = create_resp.json()["id"]

    resp = await client.get(f"/api/media/{media_id}/image")
    assert resp.status_code == 200
    body = resp.json()
    assert "image_url" in body


@pytest.mark.asyncio
async def test_get_image_not_found(client):
    """Image endpoint returns 404 for non-existent item."""
    resp = await client.get("/api/media/9999/image")
    assert resp.status_code == 404
