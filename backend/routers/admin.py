"""Admin router — exposes admin-only endpoints for global statistics."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.dependencies import require_admin
from backend.models.user import User
from backend.schemas.admin import AdminStatsResponse
from backend.services.admin_stats_service import AdminStatsService

router = APIRouter(prefix="/api/admin", tags=["admin"])

_admin_stats_service = AdminStatsService()


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_admin),
) -> AdminStatsResponse:
    """Return global application statistics for admin users."""
    return await _admin_stats_service.get_admin_stats(session)
