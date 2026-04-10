"""Explore catalog router — global catalog and add-to-shelf endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.dependencies import get_current_user
from backend.models.media import MediaItem
from backend.models.user import User
from backend.schemas.explore import ExploreAddRequest, ExploreResult
from backend.schemas.media import MediaResponse, MediaType
from backend.services.explore_service import ExploreService
from backend.services.image_service import ImageService
from backend.services.media_service import _to_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/explore", tags=["explore"])

_explore_service = ExploreService()
_image_service = ImageService()

_VALID_SORTS = {"title_asc", "title_desc", "friends"}


@router.get("", response_model=ExploreResult)
async def list_explore(
    media_type: MediaType | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("title_asc"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ExploreResult:
    """Return the deduplicated global catalog with social signals.

    Args:
        media_type: Optional filter by media type.
        search: Optional case-insensitive partial title search.
        sort: Sorting criterion (title_asc, title_desc, friends).
        page: Page number (1-indexed).
        size: Items per page (1-100).
        session: Async database session.
        user: Authenticated user.

    Returns:
        Paginated ExploreResult.

    Raises:
        HTTPException: 400 if sort value is invalid, 401 if not authenticated.
    """
    if sort not in _VALID_SORTS:
        raise HTTPException(
            status_code=400,
            detail="Invalid sort. Allowed: title_asc, title_desc, friends",
        )

    mt_value = media_type.value if media_type is not None else None

    return await _explore_service.list_global(
        session,
        user_id=user.id,
        media_type=mt_value,
        search=search,
        sort=sort,
        page=page,
        size=size,
    )


@router.post("/add", response_model=MediaResponse, status_code=201)
async def add_from_explore(
    data: ExploreAddRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> MediaResponse:
    """Add an explore item to the user's catalog as 'pending'.

    Tries to fetch a representative image after creation.

    Args:
        data: Validated add-to-shelf payload.
        session: Async database session.
        user: Authenticated user.

    Returns:
        The created MediaResponse with status 201.

    Raises:
        HTTPException: 409 if the user already owns this title+type.
    """
    result = await _explore_service.add_to_shelf(session, user.id, data)

    # Attempt to fetch an image (best-effort, same pattern as media router)
    try:
        image_filename = await _image_service.fetch_image(
            data.title, data.media_type.value,
        )
        item = await session.get(MediaItem, result.id)
        if item is not None:
            item.image_path = image_filename
            await session.commit()
            await session.refresh(item)
            return _to_response(item)
    except Exception:
        logger.exception("Image fetch failed for explore add '%s'", data.title)

    return result
