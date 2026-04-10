"""Integration tests para el router de recomendaciones."""

from __future__ import annotations

import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import (
    create_async_engine,
)

from backend.models.media import Base
from backend.models.recommendation import Recommendation  # noqa: F401
from backend.models.user import friendships

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Crea un engine in-memory con las tablas y dos usuarios de prueba."""
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with eng.begin() as conn:
        # Usuario 1 (autenticado por defecto) y usuario 2 (amigo)
        await conn.execute(
            sa.text(
                "INSERT INTO users (id, email, username, password_hash) VALUES "
                "(1, 'alice@test.com', 'alice', 'fakehash'), "
                "(2, 'bob@test.com', 'bob', 'fakehash'), "
                "(3, 'carol@test.com', 'carol', 'fakehash')"
            )
        )
        # Amistad bidireccional entre alice(1) y bob(2)
        await conn.execute(
            insert(friendships).values([
                {"user_id": 1, "friend_id": 2},
                {"user_id": 2, "friend_id": 1},
            ])
        )
        # Media item propiedad de alice
        await conn.execute(
            sa.text(
                "INSERT INTO media_items (id, user_id, title, media_type, status) "
                "VALUES (1, 1, 'Inception', 'movie', 'pending')"
            )
        )
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def client(engine):
    """Provee un AsyncClient HTTP conectado a la app con DB de prueba."""
    factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False,
    )

    async def _override_session():
        async with factory() as sess:
            yield sess

    async def _override_user():
        return User(
            id=1, email="alice@test.com", username="alice", password_hash="fakehash",
        )

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = _override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


def _client_as_user(user_id: int, email: str, username: str):
    """Helper para cambiar el usuario autenticado."""

    async def _override():
        return User(
            id=user_id, email=email, username=username, password_hash="fakehash",
        )

    return _override


# ── POST /api/recommendations ────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_recommendation_201(client):
    """Enviar una recomendación válida a un amigo retorna 201."""
    payload = {
        "receiver_id": 2,
        "media_item_id": 1,
        "message": "¡Te va a encantar!",
    }
    resp = await client.post("/api/recommendations", json=payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["sender"]["id"] == 1
    assert body["receiver"]["id"] == 2
    assert body["media_item"]["id"] == 1
    assert body["is_read"] is False
    assert body["message"] == "¡Te va a encantar!"


@pytest.mark.asyncio
async def test_send_self_recommendation_400(client):
    """Auto-recomendación retorna 400."""
    payload = {"receiver_id": 1, "media_item_id": 1}
    resp = await client.post("/api/recommendations", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_send_not_friends_403(client):
    """Recomendar a alguien que no es amigo retorna 403."""
    # carol(3) no es amiga de alice(1)
    payload = {"receiver_id": 3, "media_item_id": 1}
    resp = await client.post("/api/recommendations", json=payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_send_duplicate_409(client):
    """Enviar la misma recomendación dos veces retorna 409."""
    payload = {"receiver_id": 2, "media_item_id": 1}
    resp1 = await client.post("/api/recommendations", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/recommendations", json=payload)
    assert resp2.status_code == 409


# ── GET /api/recommendations ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_received_200(client):
    """Listar recomendaciones recibidas retorna 200 con estructura paginada."""
    # Enviar una recomendación de alice a bob
    await client.post(
        "/api/recommendations",
        json={"receiver_id": 2, "media_item_id": 1},
    )

    # Cambiar a bob para listar sus recomendaciones recibidas
    app.dependency_overrides[get_current_user] = _client_as_user(
        2, "bob@test.com", "bob",
    )

    resp = await client.get("/api/recommendations")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 1
    assert body["items"][0]["receiver"]["id"] == 2


# ── GET /api/recommendations/unread-count ────────────────────────────


@pytest.mark.asyncio
async def test_unread_count_200(client):
    """Obtener conteo de no leídas retorna 200 con count."""
    resp = await client.get("/api/recommendations/unread-count")
    assert resp.status_code == 200
    body = resp.json()
    assert "count" in body
    assert isinstance(body["count"], int)


# ── PATCH /api/recommendations/{id}/read ─────────────────────────────


@pytest.mark.asyncio
async def test_mark_as_read_200(client):
    """Marcar una recomendación como leída retorna 200 con is_read=True."""
    # Enviar recomendación de alice a bob
    send_resp = await client.post(
        "/api/recommendations",
        json={"receiver_id": 2, "media_item_id": 1},
    )
    rec_id = send_resp.json()["id"]

    # Cambiar a bob para marcar como leída
    app.dependency_overrides[get_current_user] = _client_as_user(
        2, "bob@test.com", "bob",
    )

    resp = await client.patch(f"/api/recommendations/{rec_id}/read")
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


@pytest.mark.asyncio
async def test_mark_as_read_wrong_user_404(client):
    """Marcar como leída una recomendación ajena retorna 404."""
    # Enviar recomendación de alice a bob
    send_resp = await client.post(
        "/api/recommendations",
        json={"receiver_id": 2, "media_item_id": 1},
    )
    rec_id = send_resp.json()["id"]

    # alice (sender, no receiver) intenta marcar como leída → 404
    resp = await client.patch(f"/api/recommendations/{rec_id}/read")
    assert resp.status_code == 404


# ── POST /api/recommendations/mark-all-read ──────────────────────────


@pytest.mark.asyncio
async def test_mark_all_read_200(client):
    """Marcar todas como leídas retorna 200."""
    resp = await client.post("/api/recommendations/mark-all-read")
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "All recommendations marked as read"
