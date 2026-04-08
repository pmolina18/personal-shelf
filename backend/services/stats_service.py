"""Statistics service for catalog-level aggregations."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.media import MediaItem
from backend.schemas.media import CatalogStats, MediaStatus, MediaType


class StatsService:
    """Service for computing catalog statistics.

    Provides aggregated counts and averages across all media items.
    """

    async def get_stats(self, session: AsyncSession) -> CatalogStats:
        """Compute catalog statistics.

        Returns counts grouped by media type and status, and average
        rating grouped by media type (only items with an assigned rating).

        Args:
            session: The async database session.

        Returns:
            A CatalogStats with by_type, by_status, and avg_rating_by_type.
        """
        # Count by media_type
        type_query = (
            select(MediaItem.media_type, func.count())
            .group_by(MediaItem.media_type)
        )
        type_result = await session.execute(type_query)
        by_type_raw = {row[0]: row[1] for row in type_result.all()}

        # Ensure all media types are present (default 0)
        by_type: dict[str, int] = {
            t.value: by_type_raw.get(t.value, 0) for t in MediaType
        }

        # Count by status
        status_query = (
            select(MediaItem.status, func.count())
            .group_by(MediaItem.status)
        )
        status_result = await session.execute(status_query)
        by_status_raw = {row[0]: row[1] for row in status_result.all()}

        # Ensure all statuses are present (default 0)
        by_status: dict[str, int] = {
            s.value: by_status_raw.get(s.value, 0) for s in MediaStatus
        }

        # Average rating by media_type (only items with rating)
        avg_query = (
            select(MediaItem.media_type, func.avg(MediaItem.rating))
            .where(MediaItem.rating.isnot(None))
            .group_by(MediaItem.media_type)
        )
        avg_result = await session.execute(avg_query)
        avg_raw = {row[0]: float(row[1]) for row in avg_result.all()}

        avg_rating_by_type: dict[str, float | None] = {
            t.value: avg_raw.get(t.value, None) for t in MediaType
        }

        return CatalogStats(
            by_type=by_type,
            by_status=by_status,
            avg_rating_by_type=avg_rating_by_type,
        )
