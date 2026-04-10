# Feature: friend-recommendations, Property 1: solo se puede recomendar a amigos confirmados
# Feature: friend-recommendations, Property 2: no se puede duplicar recomendación
# Feature: friend-recommendations, Property 3: unread count consistente con estado real
# Feature: friend-recommendations, Property 4: mark-as-read reduce count en 1
# Feature: friend-recommendations, Property 5: mark-all-read deja count en 0
# Feature: friend-recommendations, Property 6: no auto-recomendación
"""Property tests para recomendaciones entre amigos (Properties 1-6).

Valida: Requisitos 4.1, 4.2, 4.3, 4.7, 4.8, 4.9
"""
from __future__ import annotations


from sqlalchemy import insert
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.models.media import Base, MediaItem
from backend.models.recommendation import Recommendation  # noqa: F401
from backend.models.user import User, friendships


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _fresh_session():
    """Create an in-memory SQLite async session for test isolation."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _create_user(session: AsyncSession, username: str, email: str) -> User:
    """Crea un usuario de prueba y lo retorna."""
    user = User(username=username, email=email, password_hash="fakehash")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _create_media_item(
    session: AsyncSession,
    user_id: int,
    title: str = "Test Item",
    media_type: str = "movie",
) -> MediaItem:
    """Crea un media item de prueba y lo retorna."""
    item = MediaItem(user_id=user_id, title=title, media_type=media_type)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def _create_friendship(session: AsyncSession, user1_id: int, user2_id: int) -> None:
    """Crea amistad bidireccional entre dos usuarios."""
    await session.execute(insert(friendships).values(user_id=user1_id, friend_id=user2_id))
    await session.execute(insert(friendships).values(user_id=user2_id, friend_id=user1_id))
    await session.commit()


# ---------------------------------------------------------------------------
# Property 1: Solo amigos pueden recomendar → 403
# ---------------------------------------------------------------------------


@given(msg=st.one_of(st.none(), st.text(min_size=1, max_size=100)))
@settings(max_examples=100, deadline=None)
def test_only_friends_can_recommend(msg):
    """Sin amistad confirmada, send() debe lanzar 403.

    Validates: Requisito 4.1
    """

    async def _run():
        async for session in _fresh_session():
            sender = await _create_user(session, "sender", "sender@test.com")
            receiver = await _create_user(session, "receiver", "receiver@test.com")
            item = await _create_media_item(session, sender.id)

            # NO friendship created
            svc = RecommendationService()
            data = RecommendationCreate(
                receiver_id=receiver.id, media_item_id=item.id, message=msg,
            )
            with pytest.raises(HTTPException) as exc:
                await svc.send(session, sender.id, data)
            assert exc.value.status_code == 403

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Property 2: No duplicar recomendación → 409
# ---------------------------------------------------------------------------


@given(msg=st.one_of(st.none(), st.text(min_size=1, max_size=100)))
@settings(max_examples=100, deadline=None)
def test_no_duplicate_recommendation(msg):
    """Enviar la misma recomendación dos veces debe lanzar 409.

    Validates: Requisito 4.3
    """

    async def _run():
        async for session in _fresh_session():
            sender = await _create_user(session, "sender", "sender@test.com")
            receiver = await _create_user(session, "receiver", "receiver@test.com")
            item = await _create_media_item(session, sender.id)
            await _create_friendship(session, sender.id, receiver.id)

            svc = RecommendationService()
            data = RecommendationCreate(
                receiver_id=receiver.id, media_item_id=item.id, message=msg,
            )

            # Primera vez: éxito
            await svc.send(session, sender.id, data)

            # Segunda vez: 409
            with pytest.raises(HTTPException) as exc:
                await svc.send(session, sender.id, data)
            assert exc.value.status_code == 409

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Property 3: Unread count consistente con estado real
# ---------------------------------------------------------------------------


@given(read_states=st.lists(st.booleans(), min_size=1, max_size=10))
@settings(max_examples=100, deadline=None)
def test_unread_count_consistent(read_states):
    """El conteo de no leídas debe coincidir con la cantidad real de is_read=False.

    Validates: Requisito 4.7
    """

    async def _run():
        async for session in _fresh_session():
            sender = await _create_user(session, "sender", "sender@test.com")
            receiver = await _create_user(session, "receiver", "receiver@test.com")
            await _create_friendship(session, sender.id, receiver.id)

            svc = RecommendationService()
            expected_unread = 0

            for i, is_read in enumerate(read_states):
                item = await _create_media_item(
                    session, sender.id, title=f"Item {i}", media_type="movie",
                )
                rec = Recommendation(
                    sender_id=sender.id,
                    receiver_id=receiver.id,
                    media_item_id=item.id,
                    is_read=is_read,
                )
                session.add(rec)
                if not is_read:
                    expected_unread += 1

            await session.commit()

            count = await svc.get_unread_count(session, receiver.id)
            assert count == expected_unread

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Property 4: Mark-as-read reduce count en 1
# ---------------------------------------------------------------------------


@given(read_states=st.lists(st.booleans(), min_size=1, max_size=10))
@settings(max_examples=100, deadline=None)
def test_mark_read_decrements_count(read_states):
    """Marcar una recomendación no leída como leída debe decrementar el count en 1.

    Validates: Requisito 4.8
    """

    async def _run():
        async for session in _fresh_session():
            sender = await _create_user(session, "sender", "sender@test.com")
            receiver = await _create_user(session, "receiver", "receiver@test.com")
            await _create_friendship(session, sender.id, receiver.id)

            svc = RecommendationService()
            unread_rec_id = None

            for i, is_read in enumerate(read_states):
                item = await _create_media_item(
                    session, sender.id, title=f"Item {i}", media_type="book",
                )
                rec = Recommendation(
                    sender_id=sender.id,
                    receiver_id=receiver.id,
                    media_item_id=item.id,
                    is_read=is_read,
                )
                session.add(rec)
                await session.commit()
                await session.refresh(rec)
                if not is_read and unread_rec_id is None:
                    unread_rec_id = rec.id

            count_before = await svc.get_unread_count(session, receiver.id)

            if unread_rec_id is not None:
                await svc.mark_as_read(session, receiver.id, unread_rec_id)
                count_after = await svc.get_unread_count(session, receiver.id)
                assert count_after == count_before - 1

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Property 5: Mark-all-read → count = 0
# ---------------------------------------------------------------------------


@given(read_states=st.lists(st.booleans(), min_size=1, max_size=10))
@settings(max_examples=100, deadline=None)
def test_mark_all_read_zeroes_count(read_states):
    """Después de mark_all_as_read, el conteo de no leídas debe ser 0.

    Validates: Requisito 4.9
    """

    async def _run():
        async for session in _fresh_session():
            sender = await _create_user(session, "sender", "sender@test.com")
            receiver = await _create_user(session, "receiver", "receiver@test.com")
            await _create_friendship(session, sender.id, receiver.id)

            svc = RecommendationService()

            for i, is_read in enumerate(read_states):
                item = await _create_media_item(
                    session, sender.id, title=f"Item {i}", media_type="series",
                )
                rec = Recommendation(
                    sender_id=sender.id,
                    receiver_id=receiver.id,
                    media_item_id=item.id,
                    is_read=is_read,
                )
                session.add(rec)

            await session.commit()

            await svc.mark_all_as_read(session, receiver.id)
            count = await svc.get_unread_count(session, receiver.id)
            assert count == 0

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Property 6: No auto-recomendación → 400
# ---------------------------------------------------------------------------


@given(msg=st.one_of(st.none(), st.text(min_size=1, max_size=100)))
@settings(max_examples=100, deadline=None)
def test_no_self_recommendation(msg):
    """Intentar recomendarse a uno mismo debe lanzar 400.

    Validates: Requisito 4.2
    """

    async def _run():
        async for session in _fresh_session():
            user = await _create_user(session, "solo", "solo@test.com")
            item = await _create_media_item(session, user.id)

            svc = RecommendationService()
            data = RecommendationCreate(
                receiver_id=user.id, media_item_id=item.id, message=msg,
            )
            with pytest.raises(HTTPException) as exc:
                await svc.send(session, user.id, data)
            assert exc.value.status_code == 400

    asyncio.run(_run())
