"""Unit tests for the friends router endpoints.

Tests: send request, accept, reject, list pending, list friends,
remove friend, search users, and error cases (400, 403, 404, 409).

Uses httpx.AsyncClient + ASGITransport with app.dependency_overrides.
"""

import pytest
import pytest_asyncio
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

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# Mutable container so the override can be switched mid-test
_current_user_id: dict[str, int] = {"uid": 1}


@pytest_asyncio.fixture
async def setup():
    """Create a fresh in-memory DB with three test users and wire overrides."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Seed three users
    async with factory() as sess:
        for uid, email, uname in [
            (1, "alice@test.com", "alice"),
            (2, "bob@test.com", "bob"),
            (3, "carol@test.com", "carol"),
        ]:
            sess.add(User(id=uid, email=email, username=uname, password_hash="fakehash"))
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


# -- Send request tests -------------------------------------------------------


@pytest.mark.asyncio
async def test_send_request_success(client):
    """POST /api/friends/requests with valid username returns 201."""
    as_user(1)
    resp = await client.post("/api/friends/requests", json={"username": "bob"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["from_user"]["id"] == 1
    assert data["from_user"]["username"] == "alice"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_send_request_self_400(client):
    """POST /api/friends/requests to self returns 400."""
    as_user(1)
    resp = await client.post("/api/friends/requests", json={"username": "alice"})
    assert resp.status_code == 400
    assert "yourself" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_send_request_not_found_404(client):
    """POST /api/friends/requests to nonexistent user returns 404."""
    as_user(1)
    resp = await client.post("/api/friends/requests", json={"username": "nobody"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_send_request_duplicate_409(client):
    """POST /api/friends/requests duplicate pending returns 409."""
    as_user(1)
    await client.post("/api/friends/requests", json={"username": "bob"})
    resp = await client.post("/api/friends/requests", json={"username": "bob"})
    assert resp.status_code == 409


# -- Accept / Reject tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_accept_request_success(client):
    """POST /api/friends/requests/{id}/accept returns 200 and creates friendship."""
    as_user(1)
    send_resp = await client.post("/api/friends/requests", json={"username": "bob"})
    request_id = send_resp.json()["id"]

    # Bob accepts
    as_user(2)
    resp = await client.post(f"/api/friends/requests/{request_id}/accept")
    assert resp.status_code == 200

    # Alice should see Bob as friend
    as_user(1)
    alice_friends = await client.get("/api/friends")
    assert any(f["id"] == 2 for f in alice_friends.json())

    # Bob should see Alice as friend
    as_user(2)
    bob_friends = await client.get("/api/friends")
    assert any(f["id"] == 1 for f in bob_friends.json())


@pytest.mark.asyncio
async def test_reject_request_success(client):
    """POST /api/friends/requests/{id}/reject returns 200, no friendship."""
    as_user(1)
    send_resp = await client.post("/api/friends/requests", json={"username": "bob"})
    request_id = send_resp.json()["id"]

    as_user(2)
    resp = await client.post(f"/api/friends/requests/{request_id}/reject")
    assert resp.status_code == 200

    # Neither should be friends
    as_user(1)
    assert len((await client.get("/api/friends")).json()) == 0
    as_user(2)
    assert len((await client.get("/api/friends")).json()) == 0


@pytest.mark.asyncio
async def test_accept_request_not_recipient_403(client):
    """POST /api/friends/requests/{id}/accept by non-recipient returns 403."""
    as_user(1)
    send_resp = await client.post("/api/friends/requests", json={"username": "bob"})
    request_id = send_resp.json()["id"]

    # Carol tries to accept Alice→Bob request
    as_user(3)
    resp = await client.post(f"/api/friends/requests/{request_id}/accept")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_reject_request_not_recipient_403(client):
    """POST /api/friends/requests/{id}/reject by non-recipient returns 403."""
    as_user(1)
    send_resp = await client.post("/api/friends/requests", json={"username": "bob"})
    request_id = send_resp.json()["id"]

    as_user(3)
    resp = await client.post(f"/api/friends/requests/{request_id}/reject")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_accept_request_not_found_404(client):
    """POST /api/friends/requests/9999/accept returns 404."""
    as_user(2)
    resp = await client.post("/api/friends/requests/9999/accept")
    assert resp.status_code == 404


# -- List pending tests --------------------------------------------------------


@pytest.mark.asyncio
async def test_list_pending_requests(client):
    """GET /api/friends/requests/pending returns received requests."""
    # Alice and Carol send requests to Bob
    as_user(1)
    await client.post("/api/friends/requests", json={"username": "bob"})
    as_user(3)
    await client.post("/api/friends/requests", json={"username": "bob"})

    as_user(2)
    resp = await client.get("/api/friends/requests/pending")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    sender_ids = {r["from_user"]["id"] for r in data}
    assert sender_ids == {1, 3}


# -- List friends tests --------------------------------------------------------


@pytest.mark.asyncio
async def test_list_friends(client):
    """GET /api/friends returns confirmed friends."""
    as_user(1)
    send_resp = await client.post("/api/friends/requests", json={"username": "bob"})
    as_user(2)
    await client.post(f"/api/friends/requests/{send_resp.json()['id']}/accept")

    as_user(1)
    resp = await client.get("/api/friends")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == 2
    assert data[0]["username"] == "bob"


# -- Remove friend tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_friend_success(client):
    """DELETE /api/friends/{id} removes bidirectional friendship."""
    as_user(1)
    send_resp = await client.post("/api/friends/requests", json={"username": "bob"})
    as_user(2)
    await client.post(f"/api/friends/requests/{send_resp.json()['id']}/accept")

    as_user(1)
    resp = await client.delete("/api/friends/2")
    assert resp.status_code == 204

    # Neither should see the other
    as_user(1)
    assert len((await client.get("/api/friends")).json()) == 0
    as_user(2)
    assert len((await client.get("/api/friends")).json()) == 0


@pytest.mark.asyncio
async def test_remove_friend_not_found_404(client):
    """DELETE /api/friends/999 when not friends returns 404."""
    as_user(1)
    resp = await client.delete("/api/friends/999")
    assert resp.status_code == 404


# -- Search users tests --------------------------------------------------------


@pytest.mark.asyncio
async def test_search_users(client):
    """GET /api/friends/search?q=bob returns matching users, excludes self."""
    as_user(1)
    resp = await client.get("/api/friends/search", params={"q": "bob"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["username"] == "bob"
    assert all(u["id"] != 1 for u in data)


@pytest.mark.asyncio
async def test_search_users_no_results(client):
    """GET /api/friends/search?q=zzz returns empty list."""
    as_user(1)
    resp = await client.get("/api/friends/search", params={"q": "zzz"})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_send_request_already_friends_409(client):
    """POST /api/friends/requests when already friends returns 409."""
    as_user(1)
    send_resp = await client.post("/api/friends/requests", json={"username": "bob"})
    as_user(2)
    await client.post(f"/api/friends/requests/{send_resp.json()['id']}/accept")

    as_user(1)
    resp = await client.post("/api/friends/requests", json={"username": "bob"})
    assert resp.status_code == 409
