# Feature: backend-datetime-image-fix, Property 1: Bug Condition — Datetimes naive en updates
"""Bug condition exploration test for datetime timezone incompatibility.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5

This test verifies that after calling update_status, update_rating, and
update_tags, the datetimes assigned by the service code are naive
(tzinfo is None).

On UNFIXED code this test is EXPECTED TO FAIL because datetime.now(timezone.utc)
produces tz-aware datetimes incompatible with TIMESTAMP WITHOUT TIME ZONE columns.

NOTE: SQLite silently strips tzinfo on round-trip, masking the bug that occurs
with PostgreSQL + asyncpg. To detect the bug in tests, we intercept the datetime
values assigned by the service before they are round-tripped through the DB.
We patch `datetime` in the service module to capture the actual values produced.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.models.media import Base
from backend.schemas.media import MediaCreate, MediaType
from backend.services.media_service import MediaService

# -- Strategies --------------------------------------------------------------

valid_media_types = st.sampled_from(
    [MediaType.movie, MediaType.book, MediaType.series]
)

simple_media_create = st.builds(
    MediaCreate,
    title=st.text(min_size=1, max_size=60).filter(lambda t: t.strip()),
    media_type=valid_media_types,
    year=st.none(),
    creator=st.none(),
    notes=st.none(),
    tags=st.just([]),
)

valid_status_values = st.sampled_from(["pending", "in_progress", "completed"])

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


async def _fresh_session():
    """Create a throwaway in-memory DB and yield a session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()


class _DatetimeCapture:
    """Wrapper around the real datetime class that captures values produced
    by now() and utcnow() so we can inspect them after the service runs."""

    def __init__(self):
        self.captured_values: list[datetime] = []

    def make_wrapper(self):
        """Return a class that behaves like datetime but captures now()/utcnow() calls."""
        capture = self

        class WrappedDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                result = datetime.now(tz)
                capture.captured_values.append(result)
                return result

            @classmethod
            def utcnow(cls):
                result = datetime.utcnow()
                capture.captured_values.append(result)
                return result

        return WrappedDatetime


# -- Bug Condition: update_status produces naive datetimes -------------------


@settings(max_examples=10, deadline=None)
@given(
    create_data=simple_media_create,
    status=valid_status_values,
)
def test_update_status_produces_naive_datetimes(create_data, status):
    """After update_status, all datetime values assigned by the service
    must have tzinfo is None (naive datetimes).

    **Validates: Requirements 1.1, 1.2**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data)

            capture = _DatetimeCapture()
            with patch(
                "backend.services.media_service.datetime",
                capture.make_wrapper(),
            ):
                await svc.update_status(sess, created.id, status)

            # Every datetime produced by the service must be naive
            for dt_val in capture.captured_values:
                assert dt_val.tzinfo is None, (
                    f"Service produced tz-aware datetime {dt_val!r} "
                    f"(tzinfo={dt_val.tzinfo!r}) during update_status('{status}') "
                    f"— expected naive datetime (tzinfo=None)"
                )

    asyncio.run(_run())


# -- Bug Condition: update_rating produces naive datetimes -------------------


@settings(max_examples=10, deadline=None)
@given(
    create_data=simple_media_create,
    rating=st.integers(min_value=1, max_value=10),
)
def test_update_rating_produces_naive_datetimes(create_data, rating):
    """After update_rating, all datetime values assigned by the service
    must have tzinfo is None.

    **Validates: Requirements 1.3**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data)

            capture = _DatetimeCapture()
            with patch(
                "backend.services.media_service.datetime",
                capture.make_wrapper(),
            ):
                await svc.update_rating(sess, created.id, rating)

            for dt_val in capture.captured_values:
                assert dt_val.tzinfo is None, (
                    f"Service produced tz-aware datetime {dt_val!r} "
                    f"(tzinfo={dt_val.tzinfo!r}) during update_rating({rating}) "
                    f"— expected naive datetime (tzinfo=None)"
                )

    asyncio.run(_run())


# -- Bug Condition: update_tags produces naive datetimes ---------------------


@settings(max_examples=10, deadline=None)
@given(
    create_data=simple_media_create,
    tags=st.lists(
        st.text(min_size=1, max_size=30), max_size=10, unique=True
    ),
)
def test_update_tags_produces_naive_datetimes(create_data, tags):
    """After update_tags, all datetime values assigned by the service
    must have tzinfo is None.

    **Validates: Requirements 1.4**
    """

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            created = await svc.create(sess, create_data)

            capture = _DatetimeCapture()
            with patch(
                "backend.services.media_service.datetime",
                capture.make_wrapper(),
            ):
                await svc.update_tags(sess, created.id, tags)

            for dt_val in capture.captured_values:
                assert dt_val.tzinfo is None, (
                    f"Service produced tz-aware datetime {dt_val!r} "
                    f"(tzinfo={dt_val.tzinfo!r}) during update_tags({tags!r}) "
                    f"— expected naive datetime (tzinfo=None)"
                )

    asyncio.run(_run())
