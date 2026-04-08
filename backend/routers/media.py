"""Media CRUD router — handles HTTP concerns for media item endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from backend.db import get_session
from backend.models.media import MediaItem
from backend.schemas.media import (
    MediaCreate,
    MediaFilters,
    MediaResponse,
    MediaStatus,
    MediaType,
    MediaUpdate,
    PaginatedResult,
    RatingUpdate,
    StatusUpdate,
    TagsUpdate,
)
from backend.services.image_service import ImageService
from backend.services.media_service import MediaService, _to_response

router = APIRouter(prefix="/api/media", tags=["media"])

_media_service = MediaService()
_image_service = ImageService()


@router.post("", response_model=MediaResponse, status_code=201)
async def create_media(
    data: MediaCreate,
    session: AsyncSession = Depends(get_session),
) -> MediaResponse:
    """Create a new media item.

    Automatically fetches a representative image after creation.

    Args:
        data: Validated creation payload.
        session: Async database session.

    Returns:
        The created media item with a 201 status code.
    """
    result = await _media_service.create(session, data)

    # Fetch an image for the new item and persist the path
    image_filename = await _image_service.fetch_image(
        data.title, data.media_type.value,
    )
    item = await session.get(MediaItem, result.id)
    if item is not None:
        item.image_path = image_filename
        await session.commit()
        await session.refresh(item)
        return _to_response(item)

    return result


@router.get("", response_model=PaginatedResult)
async def list_media(
    media_type: MediaType | None = Query(None),
    status: MediaStatus | None = Query(None),
    search: str | None = Query(None),
    tag: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> PaginatedResult:
    """Return a paginated, filtered list of media items.

    Args:
        media_type: Optional media type filter.
        status: Optional status filter.
        search: Optional case-insensitive title search.
        tag: Optional tag name filter.
        page: Page number (1-indexed).
        size: Items per page.
        session: Async database session.

    Returns:
        Paginated result with matching media items.
    """
    filters = MediaFilters(
        media_type=media_type,
        status=status,
        search=search,
        tag=tag,
    )
    return await _media_service.list(session, filters, page, size)


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: int,
    session: AsyncSession = Depends(get_session),
) -> MediaResponse:
    """Fetch a single media item by ID.

    Args:
        media_id: The item's primary key.
        session: Async database session.

    Returns:
        The media item.
    """
    return await _media_service.get(session, media_id)


@router.put("/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: int,
    data: MediaUpdate,
    session: AsyncSession = Depends(get_session),
) -> MediaResponse:
    """Update an existing media item.

    Triggers a new image fetch when title or media_type changes.

    Args:
        media_id: The item's primary key.
        data: Validated update payload.
        session: Async database session.

    Returns:
        The updated media item.
    """
    result = await _media_service.update(session, media_id, data)

    # Re-fetch image when title or media_type changed
    changed_fields = data.model_dump(exclude_unset=True)
    if "title" in changed_fields or "media_type" in changed_fields:
        image_filename = await _image_service.fetch_image(
            result.title, result.media_type.value,
        )
        item = await session.get(MediaItem, result.id)
        if item is not None:
            item.image_path = image_filename
            await session.commit()
            await session.refresh(item)
            return _to_response(item)

    return result


@router.delete("/{media_id}", status_code=204)
async def delete_media(
    media_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete a media item by ID.

    Args:
        media_id: The item's primary key.
        session: Async database session.

    Returns:
        Empty response with 204 status code.
    """
    await _media_service.delete(session, media_id)
    return Response(status_code=204)


@router.patch("/{media_id}/status", response_model=MediaResponse)
async def update_status(
    media_id: int,
    body: StatusUpdate,
    session: AsyncSession = Depends(get_session),
) -> MediaResponse:
    """Change the consumption status of a media item.

    Automatically records started_at when transitioning to 'in_progress'
    and completed_at when transitioning to 'completed'.

    Args:
        media_id: The item's primary key.
        body: Request body containing the new status.
        session: Async database session.

    Returns:
        The updated media item.
    """
    return await _media_service.update_status(session, media_id, body.status)


@router.patch("/{media_id}/rating", response_model=MediaResponse)
async def update_rating(
    media_id: int,
    body: RatingUpdate,
    session: AsyncSession = Depends(get_session),
) -> MediaResponse:
    """Assign a rating (1-10) to a media item.

    Args:
        media_id: The item's primary key.
        body: Request body containing the rating value.
        session: Async database session.

    Returns:
        The updated media item.
    """
    return await _media_service.update_rating(session, media_id, body.rating)


@router.put("/{media_id}/tags", response_model=MediaResponse)
async def update_tags(
    media_id: int,
    body: TagsUpdate,
    session: AsyncSession = Depends(get_session),
) -> MediaResponse:
    """Replace the tags of a media item.

    Args:
        media_id: The item's primary key.
        body: Request body containing the list of tag names.
        session: Async database session.

    Returns:
        The updated media item.
    """
    return await _media_service.update_tags(session, media_id, body.tags)


@router.get("/{media_id}/image")
async def get_media_image(
    media_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return the image URL for a media item.

    Args:
        media_id: The item's primary key.
        session: Async database session.

    Returns:
        A dict with the image_url (or null if no image is set).

    Raises:
        HTTPException: 404 if the item does not exist.
    """
    from fastapi import HTTPException

    item = await session.get(MediaItem, media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    image_url = f"/images/{item.image_path}" if item.image_path else None
    return {"image_url": image_url}
