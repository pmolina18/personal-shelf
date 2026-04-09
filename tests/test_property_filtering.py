# Feature: media-tracker, Property 3: Combined filtering with AND logic
# Feature: media-tracker, Property 15: Descending order by creation date
"""Property tests for filtering, listing, and ordering (Properties 3, 15).

Validates: Requirements 2.1, 3.1, 3.2, 3.3, 3.4, 8.2
"""

import asyncio

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import sqlalchemy as sa

from backend.models.media import Base
from backend.models.user import User  # noqa: F401 — registers users table
from backend.schemas.media import (
    MediaCreate,
    MediaFilters,
    MediaStatus,
    MediaType,
)
from backend.services.media_service import MediaService

# -- Hypothesis strategies ---------------------------------------------------

valid_media_types = st.sampled_from(
    [MediaType.movie, MediaType.book, MediaType.series]
)
valid_statuses = st.sampled_from(
    [MediaStatus.pending, MediaStatus.in_progress, MediaStatus.completed]
)

valid_media_create = st.builds(
    MediaCreate,
    title=st.text(min_size=1, max_size=60).filter(lambda t: t.strip()),
    media_type=valid_media_types,
    year=st.one_of(st.none(), st.integers(min_value=1800, max_value=2100)),
    creator=st.one_of(st.none(), st.text(min_size=1, max_size=60)),
    notes=st.none(),
    tags=st.lists(st.text(min_size=1, max_size=30), max_size=3, unique=True),
)

catalog_strategy = st.lists(valid_media_create, min_size=1, max_size=8)

filter_strategy = st.builds(
    MediaFilters,
    media_type=st.one_of(st.none(), valid_media_types),
    status=st.one_of(st.none(), valid_statuses),
    search=st.one_of(
        st.none(),
        st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
            min_size=1,
            max_size=20,
        ),
    ),
    tag=st.none(),
)

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


async def _setup_catalog(svc, sess, items):
    """Create items and optionally set statuses. Returns created responses."""
    created = []
    for data in items:
        resp = await svc.create(sess, data, user_id=1)
        created.append(resp)
    return created


async def _fresh_session():
    """Create a throwaway in-memory DB and yield a session."""
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
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()


# -- Property 3 --------------------------------------------------------------


@settings(max_examples=100, deadline=None)
@given(catalog=catalog_strategy, filters=filter_strategy)
def test_combined_filtering_with_and_logic(catalog, filters):
    """For any catalog and filter combination, all returned items must
    simultaneously satisfy all applied filters (AND logic), and text
    search must be case-insensitive on the title."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            await _setup_catalog(svc, sess, catalog)

            result = await svc.list(sess, filters, page=1, size=100, user_id=1)

            for item in result.items:
                if filters.media_type is not None:
                    assert item.media_type == filters.media_type
                if filters.status is not None:
                    assert item.status == filters.status
                if filters.search:
                    assert filters.search.lower() in item.title.lower()

    asyncio.run(_run())


# -- Property 15 -------------------------------------------------------------


@settings(max_examples=100, deadline=None)
@given(catalog=catalog_strategy)
def test_descending_order_by_creation_date(catalog):
    """For any catalog with multiple items, listing must return items
    ordered by creation date descending (most recent first)."""

    async def _run():
        async for sess in _fresh_session():
            svc = MediaService()
            await _setup_catalog(svc, sess, catalog)

            result = await svc.list(
                sess, MediaFilters(), page=1, size=100, user_id=1
            )

            dates = [item.created_at for item in result.items]
            for i in range(len(dates) - 1):
                assert dates[i] >= dates[i + 1]

    asyncio.run(_run())
