"""Unit tests for image resilience — missing images on ephemeral filesystem.

Validates:
- Missing image returns 404 with JSON detail, not 500 (Req 7.1, 7.3)
- With TMDB_API_KEY configured, attempts on-demand re-download (Req 7.4)

Uses httpx.AsyncClient + ASGITransport with app.dependency_overrides,
following the same patterns as test_health_cors.py.
"""

from unittest.mock import AsyncMock, patch

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
from backend.main import app
from backend.models.media import Base
from backend.models.user import User  # noqa: F401 — registers users table

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# -- Fixtures ------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_engine():
    """Create a fresh in-memory DB engine with schema and a default user."""
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
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Override get_session with a factory backed by the test engine."""
    factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override():
        async with factory() as sess:
            yield sess

    app.dependency_overrides[get_session] = _override
    yield factory
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(test_session):
    """Yield an httpx AsyncClient wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# -- Tests: missing image returns 404 -----------------------------------------


@pytest.mark.asyncio
async def test_missing_image_returns_404(client):
    """GET /images/<nonexistent> returns 404 with JSON detail, not 500.

    Validates: Requirements 7.1, 7.3
    """
    resp = await client.get("/images/nonexistent_image_abc123.jpg")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Image not found"}


# -- Tests: re-download attempt with TMDB key ---------------------------------


@pytest.mark.asyncio
async def test_missing_image_attempts_redownload_with_tmdb_key(
    test_session, test_engine, tmp_path,
):
    """With TMDB_API_KEY set, the endpoint queries the DB and calls fetch_image.

    Validates: Requirements 7.1, 7.4
    """
    image_filename = "movie_abc123test.jpg"

    # Insert a media item whose image_path matches the requested filename
    async with test_engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO media_items "
                "(user_id, title, media_type, status, image_path) "
                "VALUES (1, 'Test Movie', 'movie', 'pending', :img)"
            ),
            {"img": image_filename},
        )

    # Use tmp_path as IMAGE_STORAGE_PATH so we can write a dummy file
    dummy_image_path = tmp_path

    # Mock fetch_image to "succeed": write a dummy file and return the filename
    async def fake_fetch_image(title, media_type):
        (dummy_image_path / image_filename).write_bytes(b"fake-image-data")
        return image_filename

    mock_fetch = AsyncMock(side_effect=fake_fetch_image)

    with (
        patch("backend.main.TMDB_API_KEY", "fake-key-for-test"),
        patch("backend.main.IMAGE_STORAGE_PATH", dummy_image_path),
        patch.object(
            app.state if hasattr(app, "state") else app,
            "__dict__",
            {},
        ) if False else patch(
            "backend.main._image_service"
        ) as mock_svc,
    ):
        mock_svc.fetch_image = mock_fetch

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get(f"/images/{image_filename}")

        # fetch_image should have been called with the item's title and media_type
        mock_fetch.assert_called_once_with("Test Movie", "movie")

        # The endpoint should return the re-downloaded image successfully
        assert resp.status_code == 200
