"""Statistics router — exposes catalog-level aggregation endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.schemas.media import CatalogStats
from backend.services.stats_service import StatsService

router = APIRouter(prefix="/api", tags=["stats"])

_stats_service = StatsService()


@router.get("/stats", response_model=CatalogStats)
async def get_stats(
    session: AsyncSession = Depends(get_session),
) -> CatalogStats:
    """Return catalog statistics.

    Includes counts grouped by media type and status, and average
    rating grouped by media type.

    Args:
        session: Async database session.

    Returns:
        Catalog statistics with by_type, by_status, and avg_rating_by_type.
    """
    return await _stats_service.get_stats(session)
