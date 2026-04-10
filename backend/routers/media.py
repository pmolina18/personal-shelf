"""Media CRUD router — handles HTTP concerns for media item endpoints."""

from __future__ import annotations

import logging

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
    MetadataCandidate,
    PaginatedResult,
    RatingUpdate,
    StatusUpdate,
    TagsUpdate,
)
from backend.services.image_service import ImageService
from backend.services.media_service import MediaService, _to_response
from backend.services.metadata_service import MetadataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/media", tags=["media"])

_media_service = MediaService()
_image_service = ImageService()
_metadata_service = MetadataService()


# --- Task 3.1: metadata-search MUST be registered before {media_id} routes ---


@router.get("/metadata-search", response_model=list[MetadataCandidate])
async def search_metadata(
    title: str = Query(..., min_length=1),
    media_type: MediaType = Query(...),
    user: User = Depends(get_current_user),
) -> list[MetadataCandidate]:
    """Busca sugerencias de metadatos en APIs externas.

    Args:
        title: Título a buscar (mínimo 1 carácter).
        media_type: Tipo de media (movie, book, series).
        user: Usuario autenticado.

    Returns:
        Lista de hasta 5 candidatos de metadatos.

    Raises:
        HTTPException: 400 si el título está vacío.
    """
    if not title or not title.strip():
        raise HTTPException(status_code=400, detail="Title must not be empty")
    return await _metadata_service.search(title, media_type.value)


@router.get("/tags", response_model=list[str])
async def list_tags(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[str]:
    """Return all unique tag names for the current user's items."""
    return await _media_service.list_tags(session, user_id=user.id)


# --- Task 3.2: create_media with metadata autofill ---


@router.post("", response_model=MediaResponse, status_code=201)
async def create_media(
    data: MediaCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> MediaResponse:
    """Create a new media item.

    Automatically fills missing year, creator, and notes from external
    metadata APIs when not provided by the user. Also fetches a
    representative image after creation.
    """
    # Autocompletar campos vacíos con metadatos externos
    if data.year is None or data.creator is None or data.notes is None:
        try:
            candidates = await _metadata_service.search(
                data.title, data.media_type.value,
            )
            if candidates:
                best = candidates[0]
                if data.year is None and best.year is not None:
                    data.year = best.year
                if data.creator is None and best.creator is not None:
                    data.creator = best.creator
                if data.notes is None and best.description is not None:
                    data.notes = best.description
        except Exception:
            logger.exception("Metadata autofill failed during creation")

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
    """Fetch a single media item by ID.

    If the item has no tags, automatically fetches genre tags from
    external metadata APIs and assigns them.
    """
    item = await session.get(MediaItem, media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Auto-assign genre tags if item has none
    if not item.tags:
        try:
            candidates = await _metadata_service.search(
                item.title, item.media_type,
            )
            if candidates and candidates[0].genres:
                tags = await _media_service._get_or_create_tags(
                    session, candidates[0].genres,
                )
                item.tags = tags
                await session.commit()
                await session.refresh(item)
        except Exception:
            logger.exception("Genre autofill failed for item %s", media_id)

    return _to_response(item)


# --- Task 4.1: update_media with metadata autofill on title/type change ---


@router.put("/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: int,
    data: MediaUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> MediaResponse:
    """Update an existing media item.

    When title or media_type changes, automatically fills missing year,
    creator, and notes from external metadata APIs (only for fields not
    explicitly provided in the update request). Also triggers a new image
    fetch when title or media_type changes.
    """
    changed = data.model_dump(exclude_unset=True)

    # Re-obtener metadatos si title o media_type cambiaron
    if "title" in changed or "media_type" in changed:
        try:
            current = await _media_service.get(session, media_id, user_id=user.id)
            effective_title = changed.get("title", current.title)
            effective_type = changed.get("media_type", current.media_type)
            if hasattr(effective_type, "value"):
                effective_type = effective_type.value

            candidates = await _metadata_service.search(
                effective_title, effective_type,
            )
            if candidates:
                best = candidates[0]
                if "year" not in changed and best.year is not None:
                    data.year = best.year
                if "creator" not in changed and best.creator is not None:
                    data.creator = best.creator
                if "notes" not in changed and best.description is not None:
                    data.notes = best.description
        except Exception:
            logger.exception("Metadata autofill failed during update")

    result = await _media_service.update(session, media_id, data, user_id=user.id)

    if "title" in changed or "media_type" in changed:
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
