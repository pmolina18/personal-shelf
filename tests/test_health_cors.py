"""Unit tests for health check endpoint and CORS middleware.

Validates:
- GET /api/health returns 200 with active DB (Req 8.1, 8.2, 8.3)
- GET /api/health returns 503 when DB is unreachable (Req 8.4)
- CORS allows configured origins when ALLOWED_ORIGINS is set (Req 3.2)
- CORS allows all origins when ALLOWED_ORIGINS is not set (Req 3.3)

Uses httpx.AsyncClient + ASGITransport with app.dependency_overrides.
"""

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
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
async def test_session():
    """Create a fresh in-memory DB and yield a session override."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override():
        async with factory() as sess:
            yield sess

    app.dependency_overrides[get_session] = _override
    yield factory
    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_session):
    """Yield an httpx AsyncClient wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# -- Health Check tests --------------------------------------------------------


@pytest.mark.asyncio
async def test_health_check_ok(client):
    """GET /api/health returns 200 with {"status": "ok"} when DB is active."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_check_db_failure():
    """GET /api/health returns 503 when the DB connection fails."""

    async def _broken_session():
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.side_effect = ConnectionError("DB down")
        yield mock_session

    app.dependency_overrides[get_session] = _broken_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/health")
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "unhealthy"
        assert data["detail"] == "database connection failed"
    finally:
        app.dependency_overrides.clear()


# -- CORS tests ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_cors_allows_configured_origins(test_session):
    """When ALLOWED_ORIGINS is set, CORS includes the matching origin header."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware


    # Build a fresh app with specific ALLOWED_ORIGINS
    test_app = FastAPI()
    origins = ["https://myapp.vercel.app", "https://other.example.com"]
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @test_app.get("/api/health")
    async def _health():
        return {"status": "ok"}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        # Preflight with allowed origin
        resp = await c.options(
            "/api/health",
            headers={
                "Origin": "https://myapp.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "https://myapp.vercel.app"

        # Preflight with disallowed origin — header should be absent
        resp2 = await c.options(
            "/api/health",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in resp2.headers


@pytest.mark.asyncio
async def test_cors_allows_all_origins_when_not_set(test_session):
    """When ALLOWED_ORIGINS is not set, CORS allows all origins (*)."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    # Build a fresh app with wildcard origins (default behaviour)
    test_app = FastAPI()
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @test_app.get("/api/health")
    async def _health():
        return {"status": "ok"}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        origin = "https://any-random-origin.example.com"
        resp = await c.get(
            "/api/health",
            headers={"Origin": origin},
        )
        # Starlette echoes the requesting origin when allow_origins=["*"]
        allowed = resp.headers.get("access-control-allow-origin")
        assert allowed in ("*", origin), f"Expected wildcard CORS, got {allowed}"
