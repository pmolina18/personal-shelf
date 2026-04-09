"""Unit tests for StatsService."""

import pytest

from backend.models.media import MediaItem
from backend.services.stats_service import StatsService


@pytest.fixture
def stats_service():
    """Return a StatsService instance."""
    return StatsService()


@pytest.mark.asyncio
async def test_get_stats_empty_catalog(session, stats_service):
    """Stats on an empty catalog return zero counts and None averages."""
    stats = await stats_service.get_stats(session, user_id=1)

    assert stats.by_type == {"movie": 0, "book": 0, "series": 0}
    assert stats.by_status == {"pending": 0, "in_progress": 0, "completed": 0}
    assert stats.avg_rating_by_type == {"movie": None, "book": None, "series": None}


@pytest.mark.asyncio
async def test_get_stats_counts_by_type(session, stats_service):
    """Counts by media_type reflect the items in the catalog."""
    session.add_all([
        MediaItem(user_id=1, title="Movie 1", media_type="movie", status="pending"),
        MediaItem(user_id=1, title="Movie 2", media_type="movie", status="pending"),
        MediaItem(user_id=1, title="Book 1", media_type="book", status="pending"),
    ])
    await session.commit()

    stats = await stats_service.get_stats(session, user_id=1)

    assert stats.by_type["movie"] == 2
    assert stats.by_type["book"] == 1
    assert stats.by_type["series"] == 0


@pytest.mark.asyncio
async def test_get_stats_counts_by_status(session, stats_service):
    """Counts by status reflect the items in the catalog."""
    session.add_all([
        MediaItem(user_id=1, title="A", media_type="movie", status="pending"),
        MediaItem(user_id=1, title="B", media_type="book", status="completed"),
        MediaItem(user_id=1, title="C", media_type="series", status="completed"),
        MediaItem(user_id=1, title="D", media_type="movie", status="in_progress"),
    ])
    await session.commit()

    stats = await stats_service.get_stats(session, user_id=1)

    assert stats.by_status["pending"] == 1
    assert stats.by_status["in_progress"] == 1
    assert stats.by_status["completed"] == 2


@pytest.mark.asyncio
async def test_get_stats_avg_rating_excludes_unrated(session, stats_service):
    """Average rating only considers items with an assigned rating."""
    session.add_all([
        MediaItem(user_id=1, title="Rated Movie", media_type="movie", status="completed", rating=8),
        MediaItem(user_id=1, title="Unrated Movie", media_type="movie", status="pending"),
        MediaItem(user_id=1, title="Rated Book", media_type="book", status="completed", rating=6),
        MediaItem(user_id=1, title="Another Book", media_type="book", status="completed", rating=10),
    ])
    await session.commit()

    stats = await stats_service.get_stats(session, user_id=1)

    assert stats.avg_rating_by_type["movie"] == 8.0
    assert stats.avg_rating_by_type["book"] == 8.0  # (6+10)/2
    assert stats.avg_rating_by_type["series"] is None
