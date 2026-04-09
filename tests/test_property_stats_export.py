# Feature: media-tracker, Property 10: Statistics consistent with the catalog
# Feature: media-tracker, Property 11: JSON round-trip
"""Property tests for statistics and export/import (Properties 10, 11).

Validates: Requirements 9.1, 9.2, 9.3, 10.4
"""

import asyncio
from collections import defaultdict

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
from backend.schemas.media import MediaCreate, MediaStatus, MediaType
from backend.services.export_service import ExportService
from backend.services.media_service import MediaService
from backend.services.stats_service import StatsService

# -- Hypothesis strategies ---------------------------------------------------

valid_media_types = st.sampled_from(
    [MediaType.movie, MediaType.book, MediaType.series]
)

valid_statuses = st.sampled_from(
    [MediaStatus.pending, MediaStatus.in_progress, MediaStatus.completed]
)

valid_media_create = st.builds(
    MediaCreate,
    title=st.text(min_size=1, max_size=100).filter(lambda t: t.strip()),
    media_type=valid_media_types,
    year=st.one_of(st.none(), st.integers(min_value=1800, max_value=2100)),
    creator=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    notes=st.one_of(st.none(), st.text(max_size=200)),
    tags=st.lists(
        st.text(min_size=1, max_size=50).filter(lambda t: t.strip()),
        max_size=5,
        unique=True,
    ),
)

# Strategy for a catalog item: media create data + optional rating + optional status
catalog_item_strategy = st.tuples(
    valid_media_create,
    st.one_of(st.none(), st.integers(min_value=1, max_value=10)),
    valid_statuses,
)

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


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


# -- Property 10: Statistics consistent with the catalog ---------------------


@settings(max_examples=100, deadline=None)
@given(
    items=st.lists(catalog_item_strategy, min_size=0, max_size=15),
)
def test_statistics_consistent_with_catalog(items):
    """**Validates: Requirements 9.1, 9.2, 9.3**

    For any catalog of Media_Items, the sum of counts grouped by Media_Type
    must equal the total number of items, the sum of counts grouped by Status
    must equal the total number of items, and the average Rating by Media_Type
    must match the manual calculation over the items that have an assigned Rating.
    """

    async def _run():
        async for sess in _fresh_session():
            media_svc = MediaService()
            stats_svc = StatsService()

            # Track what we create for manual verification
            created_types = []
            created_statuses = []
            ratings_by_type: dict[str, list[int]] = defaultdict(list)

            for create_data, rating, status in items:
                result = await media_svc.create(sess, create_data, user_id=1)
                item_id = result.id

                # Update status (need in_progress before completed for dates)
                if status != MediaStatus.pending:
                    if status == MediaStatus.completed:
                        await media_svc.update_status(
                            sess, item_id, MediaStatus.in_progress.value
                        )
                    await media_svc.update_status(sess, item_id, status.value)

                # Update rating if provided
                if rating is not None:
                    await media_svc.update_rating(sess, item_id, rating)

                created_types.append(create_data.media_type.value)
                created_statuses.append(status.value)
                if rating is not None:
                    ratings_by_type[create_data.media_type.value].append(rating)

            # Get stats from service
            stats = await stats_svc.get_stats(sess, user_id=1)

            total_items = len(items)

            # Assert: sum of by_type counts == total items
            assert sum(stats.by_type.values()) == total_items

            # Assert: sum of by_status counts == total items
            assert sum(stats.by_status.values()) == total_items

            # Assert: individual type counts match
            for mt in MediaType:
                expected_count = created_types.count(mt.value)
                assert stats.by_type[mt.value] == expected_count

            # Assert: individual status counts match
            for ms in MediaStatus:
                expected_count = created_statuses.count(ms.value)
                assert stats.by_status[ms.value] == expected_count

            # Assert: average rating by type matches manual calculation
            for mt in MediaType:
                type_ratings = ratings_by_type.get(mt.value, [])
                if type_ratings:
                    expected_avg = sum(type_ratings) / len(type_ratings)
                    actual_avg = stats.avg_rating_by_type[mt.value]
                    assert actual_avg is not None
                    assert abs(actual_avg - expected_avg) < 0.01
                else:
                    assert stats.avg_rating_by_type[mt.value] is None

    asyncio.run(_run())


# -- Property 11: JSON round-trip -------------------------------------------


@settings(max_examples=100, deadline=None)
@given(
    items=st.lists(valid_media_create, min_size=1, max_size=10),
)
def test_json_round_trip(items):
    """**Validates: Requirements 10.4**

    For any catalog of valid Media_Items, exporting to JSON and importing
    the resulting JSON must produce Media_Items equivalent to the originals
    (same fields, same values).
    """

    async def _run():
        async for sess in _fresh_session():
            media_svc = MediaService()
            export_svc = ExportService()

            # Create all items
            originals = []
            for create_data in items:
                result = await media_svc.create(sess, create_data, user_id=1)
                originals.append(result)

            # Export catalog
            exported = await export_svc.export_catalog(sess, user_id=1)

            assert exported["version"] == "1.0"
            assert len(exported["items"]) == len(originals)

            # Clear the database — delete all items and associations
            from sqlalchemy import delete

            from backend.models.media import MediaItem, Tag, media_tags

            await sess.execute(delete(media_tags))
            await sess.execute(delete(MediaItem))
            await sess.execute(delete(Tag))
            await sess.commit()

            # Import from exported JSON
            import_result = await export_svc.import_catalog(sess, exported, user_id=1)

            assert import_result.created == len(originals)
            assert len(import_result.errors) == 0

            # Fetch all imported items
            from sqlalchemy import select

            result = await sess.execute(select(MediaItem))
            imported_items = result.scalars().unique().all()

            assert len(imported_items) == len(originals)

            # Sort both lists by title for comparison (IDs may differ)
            originals_sorted = sorted(originals, key=lambda x: x.title)
            imported_sorted = sorted(imported_items, key=lambda x: x.title)

            for orig, imp in zip(originals_sorted, imported_sorted):
                assert imp.title == orig.title
                assert imp.media_type == orig.media_type.value
                assert imp.status == orig.status.value
                assert imp.rating == orig.rating
                assert imp.year == orig.year
                assert imp.creator == orig.creator
                assert imp.notes == orig.notes
                # Compare tags (sorted for order-independence)
                imp_tags = sorted([t.name for t in imp.tags])
                orig_tags = sorted(orig.tags)
                assert imp_tags == orig_tags

    asyncio.run(_run())
