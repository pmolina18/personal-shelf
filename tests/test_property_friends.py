# Feature: social-login, Property 15: Friend request creation
# Feature: social-login, Property 16: Friend request validation
# Feature: social-login, Property 17: User search by username substring
# Feature: social-login, Property 18: Accept creates bidirectional friendship
# Feature: social-login, Property 19: Reject doesn't create friendship
# Feature: social-login, Property 20: Pending requests listing
# Feature: social-login, Property 21: Authorization on request actions
# Feature: social-login, Property 22: Bidirectional removal
# Feature: social-login, Property 23: Friends listing
"""Property tests for the friendship system (Properties 15-23).

Validates: Requirements 6.1-6.5, 7.1-7.4, 8.1, 8.3
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

from backend.models.media import Base
from backend.models.user import FriendRequest, User, friendships
from backend.services.friend_service import FriendService

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

safe_chars = st.characters(whitelist_categories=("L", "N"))
username_strategy = st.text(alphabet=safe_chars, min_size=3, max_size=30).filter(
    lambda s: s.strip() and len(s) >= 3
)


async def _fresh_session():
    """Create a throwaway in-memory DB with three test users and yield a session."""
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
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()


# -- Property 15: Friend request creation -------------------------------------


@settings(max_examples=100, deadline=None)
@given(
    sender_id=st.sampled_from([1, 2]),
    receiver_name=st.sampled_from(["alice", "bob", "carol"]),
)
def test_friend_request_creation(sender_id, receiver_name):
    """Two unrelated users -> pending request with correct from/to.

    **Validates: Requirement 6.1**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = FriendService()
            result = await sess.execute(
                sa.select(User).where(User.username == receiver_name)
            )
            receiver = result.scalar_one()
            if receiver.id == sender_id:
                return
            resp = await svc.send_request(sess, sender_id, receiver_name)
            assert resp.from_user.id == sender_id
            assert resp.id is not None
            req = await sess.get(FriendRequest, resp.id)
            assert req is not None
            assert req.from_user_id == sender_id
            assert req.to_user_id == receiver.id
            assert req.status == "pending"

    asyncio.run(_run())


# -- Property 16: Friend request validation -----------------------------------


@settings(max_examples=100, deadline=None)
@given(data=st.data())
def test_friend_request_validation(data):
    """Self-request -> 400, already friends -> 409, duplicate pending -> 409.

    **Validates: Requirements 6.2, 6.3, 6.4**
    """
    from fastapi import HTTPException

    scenario = data.draw(st.sampled_from(["self", "already_friends", "duplicate"]))

    async def _run():
        async for sess in _fresh_session():
            svc = FriendService()
            if scenario == "self":
                with pytest.raises(HTTPException) as exc_info:
                    await svc.send_request(sess, 1, "alice")
                assert exc_info.value.status_code == 400
            elif scenario == "already_friends":
                await sess.execute(
                    sa.insert(friendships).values(user_id=1, friend_id=2)
                )
                await sess.execute(
                    sa.insert(friendships).values(user_id=2, friend_id=1)
                )
                await sess.commit()
                with pytest.raises(HTTPException) as exc_info:
                    await svc.send_request(sess, 1, "bob")
                assert exc_info.value.status_code == 409
            elif scenario == "duplicate":
                await svc.send_request(sess, 1, "bob")
                with pytest.raises(HTTPException) as exc_info:
                    await svc.send_request(sess, 1, "bob")
                assert exc_info.value.status_code == 409

    asyncio.run(_run())


# -- Property 17: User search by username substring ---------------------------


@settings(max_examples=100, deadline=None)
@given(query=st.sampled_from(["ali", "bob", "car", "o", "a", "xyz"]))
def test_user_search_by_username(query):
    """Results contain only substring matches (case-insensitive), exclude searcher.

    **Validates: Requirement 6.5**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = FriendService()
            searcher_id = 1
            results = await svc.search_users(sess, searcher_id, query)
            for r in results:
                assert query.lower() in r.username.lower()
                assert r.id != searcher_id
            all_result = await sess.execute(
                sa.select(User).where(
                    User.username.ilike(f"%{query}%"),
                    User.id != searcher_id,
                )
            )
            expected_ids = {u.id for u in all_result.scalars().all()}
            actual_ids = {r.id for r in results}
            assert actual_ids == expected_ids

    asyncio.run(_run())


# -- Property 18: Accept creates bidirectional friendship ---------------------


@settings(max_examples=100, deadline=None)
@given(sender_id=st.sampled_from([1, 3]))
def test_accept_creates_bidirectional_friendship(sender_id):
    """Accept -> both in each other's friend list, request deleted.

    **Validates: Requirement 7.1**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = FriendService()
            receiver_id = 2
            resp = await svc.send_request(sess, sender_id, "bob")
            request_id = resp.id
            await svc.accept_request(sess, receiver_id, request_id)
            friends_of_sender = await svc.list_friends(sess, sender_id)
            friends_of_receiver = await svc.list_friends(sess, receiver_id)
            assert receiver_id in {f.id for f in friends_of_sender}
            assert sender_id in {f.id for f in friends_of_receiver}
            req = await sess.get(FriendRequest, request_id)
            assert req is None

    asyncio.run(_run())


# -- Property 19: Reject doesn't create friendship ----------------------------


@settings(max_examples=100, deadline=None)
@given(sender_id=st.sampled_from([1, 3]))
def test_reject_does_not_create_friendship(sender_id):
    """Reject -> request deleted, neither in friend list.

    **Validates: Requirement 7.2**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = FriendService()
            receiver_id = 2
            resp = await svc.send_request(sess, sender_id, "bob")
            request_id = resp.id
            await svc.reject_request(sess, receiver_id, request_id)
            friends_of_sender = await svc.list_friends(sess, sender_id)
            friends_of_receiver = await svc.list_friends(sess, receiver_id)
            assert all(f.id != receiver_id for f in friends_of_sender)
            assert all(f.id != sender_id for f in friends_of_receiver)
            req = await sess.get(FriendRequest, request_id)
            assert req is None

    asyncio.run(_run())


# -- Property 20: Pending requests listing ------------------------------------


@settings(max_examples=100, deadline=None)
@given(
    sender_ids=st.lists(
        st.sampled_from([1, 3]), min_size=0, max_size=2, unique=True
    )
)
def test_pending_requests_listing(sender_ids):
    """N received requests -> exactly N in list with sender username.

    **Validates: Requirement 7.3**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = FriendService()
            receiver_id = 2
            for sid in sender_ids:
                await svc.send_request(sess, sid, "bob")
            pending = await svc.list_pending(sess, receiver_id)
            assert len(pending) == len(sender_ids)
            pending_sender_ids = {p.from_user.id for p in pending}
            assert pending_sender_ids == set(sender_ids)
            for p in pending:
                assert p.from_user.username is not None
                assert len(p.from_user.username) > 0

    asyncio.run(_run())


# -- Property 21: Authorization on request actions ----------------------------


@settings(max_examples=100, deadline=None)
@given(action=st.sampled_from(["accept", "reject"]))
def test_authorization_on_request_actions(action):
    """User C can't accept/reject A->B request -> 403.

    **Validates: Requirement 7.4**
    """
    from fastapi import HTTPException

    async def _run():
        async for sess in _fresh_session():
            svc = FriendService()
            resp = await svc.send_request(sess, 1, "bob")
            request_id = resp.id
            with pytest.raises(HTTPException) as exc_info:
                if action == "accept":
                    await svc.accept_request(sess, 3, request_id)
                else:
                    await svc.reject_request(sess, 3, request_id)
            assert exc_info.value.status_code == 403

    asyncio.run(_run())


# -- Property 22: Bidirectional removal ---------------------------------------


@settings(max_examples=100, deadline=None)
@given(remover=st.sampled_from([1, 2]))
def test_bidirectional_removal(remover):
    """Remove friendship -> neither in other's list.

    **Validates: Requirement 8.1**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = FriendService()
            resp = await svc.send_request(sess, 1, "bob")
            await svc.accept_request(sess, 2, resp.id)
            other = 2 if remover == 1 else 1
            await svc.remove_friend(sess, remover, other)
            friends_of_remover = await svc.list_friends(sess, remover)
            friends_of_other = await svc.list_friends(sess, other)
            assert all(f.id != other for f in friends_of_remover)
            assert all(f.id != remover for f in friends_of_other)

    asyncio.run(_run())


# -- Property 23: Friends listing ---------------------------------------------


@settings(max_examples=100, deadline=None)
@given(
    friend_ids=st.lists(
        st.sampled_from([2, 3]), min_size=0, max_size=2, unique=True
    )
)
def test_friends_listing(friend_ids):
    """N confirmed friends -> exactly N entries with id and username.

    **Validates: Requirement 8.3**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = FriendService()
            user_id = 1
            for fid in friend_ids:
                friend = await sess.get(User, fid)
                resp = await svc.send_request(sess, user_id, friend.username)
                await svc.accept_request(sess, fid, resp.id)
            friends = await svc.list_friends(sess, user_id)
            assert len(friends) == len(friend_ids)
            result_ids = {f.id for f in friends}
            assert result_ids == set(friend_ids)
            for f in friends:
                assert f.id is not None
                assert f.username is not None
                assert len(f.username) > 0

    asyncio.run(_run())
