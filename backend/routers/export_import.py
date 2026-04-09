"""Export and import router — catalog JSON serialization endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.media import ImportResult
from backend.services.export_service import ExportService

router = APIRouter(prefix="/api", tags=["export_import"])

_export_service = ExportService()


@router.get("/export")
async def export_catalog(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    """Export the authenticated user's catalog as JSON."""
    return await _export_service.export_catalog(session, user_id=user.id)


@router.post("/import", response_model=ImportResult)
async def import_catalog(
    data: dict,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ImportResult:
    """Import media items from a JSON payload for the authenticated user."""
    return await _export_service.import_catalog(session, data, user_id=user.id)
