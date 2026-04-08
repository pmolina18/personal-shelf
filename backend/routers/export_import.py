"""Export and import router — catalog JSON serialization endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.schemas.media import ImportResult
from backend.services.export_service import ExportService

router = APIRouter(prefix="/api", tags=["export_import"])

_export_service = ExportService()


@router.get("/export")
async def export_catalog(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Export the entire catalog as JSON.

    Args:
        session: Async database session.

    Returns:
        A JSON-serializable dict with version, timestamp, and all items.
    """
    return await _export_service.export_catalog(session)


@router.post("/import", response_model=ImportResult)
async def import_catalog(
    data: dict,
    session: AsyncSession = Depends(get_session),
) -> ImportResult:
    """Import media items from a JSON payload.

    Args:
        data: A dict matching the ExportData schema.
        session: Async database session.

    Returns:
        An ImportResult with the count of created items and any errors.
    """
    return await _export_service.import_catalog(session, data)
