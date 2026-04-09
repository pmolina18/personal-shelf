"""Media CRUD router — handles HTTP concerns for media item endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from backend.db import get_session
from backend.dependencies import get_current_user
from backend.models.media import MediaItem
from backend.models.user import User
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
    user: User = Depends(get_current_user),
) -> MediaResponse:
    """Create a new media item.

    Automatically fetches a representative image after creation.
    """
    result = await _media_service.create(session, data, user_id=user.id)

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
    user: User = Depends(get_current_user),
) -> PaginatedResult:
    """Return a paginated, filtered list of media items."""
    filters = MediaFilters(
        media_type=media_type,
        status=status,
        search=search,
        tag=tag,
    )
    return await _media_service.list(session, filters, page, size, user_id=user.id)


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> MediaResponse:
    """Fetch a single media item by ID."""
    return await _media_service.get(session, media_id, user_id=user.id)


@router.put("/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: int,
    data: MediaUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> MediaResponse:
    """Update an existing media item.

    Triggers a new image fetch when title or media_type changes.
    """
    result = await _media_service.update(session, media_id, data, user_id=user.id)

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
    user: User = Depends(get_current_user),
) -> Response:
    """Delete a media item by ID."""
    await _media_service.delete(session, media_id, user_id=user.id)
    return Response(status_code=204)


@router.patch("/{media_id}/status", response_model=MediaResponse)
async def update_status(
    media_id: int,
    body: StatusUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> MediaResponse:
    """Change the consumption status of a media item."""
    return await _media_service.update_status(
        session, media_id, body.status, user_id=user.id
    )


@router.patch("/{media_id}/rating", response_model=MediaResponse)
async def update_rating(
    media_id: int,
    body: RatingUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> MediaResponse:
    """Assign a rating (1-10) to a media item."""
    return await _media_service.update_rating(
        session, media_id, body.rating, user_id=user.id
    )


@router.put("/{media_id}/tags", response_model=MediaResponse)
async def update_tags(
    media_id: int,
    body: TagsUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> MediaResponse:
    """Replace the tags of a media item."""
    return await _media_service.update_tags(
        session, media_id, body.tags, user_id=user.id
    )


@router.get("/{media_id}/image")
async def get_media_image(
    media_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    """Return the image URL for a media item."""
    item = await session.get(MediaItem, media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    image_url = f"/images/{item.image_path}" if item.image_path else None
    return {"image_url": image_url}
