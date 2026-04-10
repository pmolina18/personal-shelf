"""Unit tests for the authentication router endpoints.

Tests: register (201), duplicate register (409), login (200), login failed (401),
refresh (200), refresh invalid (401).

Uses httpx.AsyncClient + ASGITransport with app.dependency_overrides.
"""

from unittest.mock import patch

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
    """Yield an httpx AsyncClient wired to the FastAPI app.

    Patches AllowedUsersService.is_allowed to always return True so
    existing registration tests are not blocked by the allowed-users gate.
    """
    transport = ASGITransport(app=app)
    with patch(
        "backend.services.auth_service.AllowedUsersService.is_allowed",
        return_value=True,
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


# -- Registration tests -------------------------------------------------------


@pytest.mark.asyncio
async def test_register_success(client):
    """POST /api/auth/register with valid data returns 201 with tokens."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "securepass123",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["username"] == "newuser"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """POST /api/auth/register with existing email returns 409."""
    payload = {
        "email": "dup@example.com",
        "username": "user1",
        "password": "securepass123",
    }
    resp1 = await client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    payload2 = {
        "email": "dup@example.com",
        "username": "user2",
        "password": "securepass123",
    }
    resp2 = await client.post("/api/auth/register", json=payload2)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    """POST /api/auth/register with existing username returns 409."""
    payload = {
        "email": "a@example.com",
        "username": "sameuser",
        "password": "securepass123",
    }
    resp1 = await client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    payload2 = {
        "email": "b@example.com",
        "username": "sameuser",
        "password": "securepass123",
    }
    resp2 = await client.post("/api/auth/register", json=payload2)
    assert resp2.status_code == 409


# -- Login tests ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success(client):
    """POST /api/auth/login with valid credentials returns 200 with tokens."""
    # Register first
    await client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "securepass123",
        },
    )

    resp = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "securepass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """POST /api/auth/login with wrong password returns 401."""
    # Register first
    await client.post(
        "/api/auth/register",
        json={
            "email": "fail@example.com",
            "username": "failuser",
            "password": "securepass123",
        },
    )

    resp = await client.post(
        "/api/auth/login",
        json={"email": "fail@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    """POST /api/auth/login with non-existent email returns 401."""
    resp = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "whatever123"},
    )
    assert resp.status_code == 401


# -- Refresh tests -------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_success(client):
    """POST /api/auth/refresh with valid refresh token returns new token pair."""
    # Register to get tokens
    reg_resp = await client.post(
        "/api/auth/register",
        json={
            "email": "refresh@example.com",
            "username": "refreshuser",
            "password": "securepass123",
        },
    )
    refresh_token = reg_resp.json()["refresh_token"]

    resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    """POST /api/auth/refresh with invalid token returns 401."""
    resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": "not-a-valid-jwt"},
    )
    assert resp.status_code == 401
