"""Statistics router — exposes catalog-level aggregation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.media import CatalogStats
from backend.services.stats_service import StatsService

router = APIRouter(prefix="/api", tags=["stats"])

_stats_service = StatsService()


@router.get("/stats", response_model=CatalogStats)
async def get_stats(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> CatalogStats:
    """Return catalog statistics for the authenticated user."""
    return await _stats_service.get_stats(session, user_id=user.id)
