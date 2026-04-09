"""Feed router — social feed and friend collection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.media import MediaFilters, MediaStatus, MediaType, PaginatedResult
from backend.schemas.social import FeedResponse
from backend.services.feed_service import FeedService

router = APIRouter(prefix="/api/feed", tags=["feed"])

_feed_service = FeedService()


@router.get("", response_model=FeedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=20),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FeedResponse:
    """Return a paginated social feed of friend activity.

    Args:
        page: Page number (1-indexed).
        size: Items per page (max 20).
        user: Authenticated user.
        session: Async database session.

    Returns:
        Paginated feed entries.
    """
    return await _feed_service.get_feed(session, user.id, page, size)


@router.get("/friends/{friend_id}/collection", response_model=PaginatedResult)
async def get_friend_collection(
    friend_id: int,
    media_type: MediaType | None = None,
    status: MediaStatus | None = None,
    search: str | None = None,
    tag: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PaginatedResult:
    """Return a friend's media collection with optional filters.

    Args:
        friend_id: ID of the friend whose collection to view.
        media_type: Filter by media type.
        status: Filter by consumption status.
        search: Case-insensitive title search.
        tag: Filter by tag name.
        page: Page number (1-indexed).
        size: Items per page.
        user: Authenticated user.
        session: Async database session.

    Returns:
        Paginated media items from the friend's collection.

    Raises:
        HTTPException: 403 if not friends.
    """
    filters = MediaFilters(
        media_type=media_type,
        status=status,
        search=search,
        tag=tag,
    )
    return await _feed_service.get_friend_collection(
        session, user.id, friend_id, filters, page, size
    )
