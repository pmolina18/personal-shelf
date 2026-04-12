"""Media service layer with CRUD operations, status, rating, and tag management."""

from __future__ import annotations

import math
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.media import MediaItem, Tag
from backend.schemas.media import (
    MediaCreate,
    MediaFilters,
    MediaResponse,
    MediaStatus,
    MediaUpdate,
    PaginatedResult,
)


def _to_response(item: MediaItem) -> MediaResponse:
    """Convert a MediaItem ORM object to a MediaResponse schema.

    Args:
        item: The SQLAlchemy MediaItem instance.

    Returns:
        A MediaResponse with tag names and image URL derived from image_path.
    """
    return MediaResponse(
        id=item.id,
        title=item.title,
        media_type=item.media_type,
        status=item.status,
        rating=item.rating,
        year=item.year,
        creator=item.creator,
        notes=item.notes,
        image_url=f"/images/{item.image_path}" if item.image_path else None,
        tags=[t.name for t in item.tags],
        created_at=item.created_at,
        updated_at=item.updated_at,
        started_at=item.started_at,
        completed_at=item.completed_at,
        pending_at=item.pending_at,
    )


class MediaService:
    """Service encapsulating all media item business logic.

    All methods receive an AsyncSession and operate within it.
    """

    async def create(
        self, session: AsyncSession, data: MediaCreate, user_id: int
    ) -> MediaResponse:
        """Create a new media item with status 'pending'.

        Args:
            session: The async database session.
            data: Validated creation payload.
            user_id: ID of the owning user.

        Returns:
            The created media item as a response schema.
        """
        item = MediaItem(
            user_id=user_id,
            title=data.title,
            media_type=data.media_type.value,
            status=MediaStatus.pending.value,
            year=data.year,
            creator=data.creator,
            notes=data.notes,
            pending_at=datetime.utcnow(),
        )

        # Handle tags if provided
        if data.tags:
            if len(data.tags) > 10:
                raise HTTPException(status_code=400, detail="Maximum 10 tags per item")
            tags = await self._get_or_create_tags(session, data.tags)
            item.tags = tags

        session.add(item)
        await session.commit()
        await session.refresh(item)
        return _to_response(item)

    async def get(
        self, session: AsyncSession, media_id: int, user_id: int
    ) -> MediaResponse:
        """Fetch a single media item by ID.

        Args:
            session: The async database session.
            media_id: The item's primary key.
            user_id: ID of the authenticated user.

        Returns:
            The media item as a response schema.

        Raises:
            HTTPException: 404 if the item does not exist, 403 if not owner.
        """
        item = await session.get(MediaItem, media_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        return _to_response(item)

    async def list(
        self,
        session: AsyncSession,
        filters: MediaFilters,
        page: int = 1,
        size: int = 20,
        user_id: int = 1,
    ) -> PaginatedResult:
        """Return a paginated, filtered list of media items.

        Items are ordered by created_at descending (most recent first).

        Args:
            session: The async database session.
            filters: Optional filters (media_type, status, search, tag).
            page: Page number (1-indexed).
            size: Items per page.
            user_id: Owner user ID to filter items by.

        Returns:
            A PaginatedResult with items, total count, and page metadata.
        """
        query = select(MediaItem).where(MediaItem.user_id == user_id)

        if filters.media_type is not None:
            query = query.where(MediaItem.media_type == filters.media_type.value)

        if filters.status is not None:
            query = query.where(MediaItem.status == filters.status.value)

        if filters.search:
            query = query.where(MediaItem.title.ilike(f"%{filters.search}%"))

        if filters.tag:
            query = query.join(MediaItem.tags).where(Tag.name.ilike(f"%{filters.tag}%"))

        # Count total matching items
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply ordering and pagination
        query = query.order_by(MediaItem.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await session.execute(query)
        items = result.scalars().unique().all()

        pages = math.ceil(total / size) if size > 0 else 0

        return PaginatedResult(
            items=[_to_response(i) for i in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def update(
        self, session: AsyncSession, media_id: int, data: MediaUpdate, user_id: int = 1
    ) -> MediaResponse:
        """Partially update an existing media item.

        Only fields present in the update payload are modified.

        Args:
            session: The async database session.
            media_id: The item's primary key.
            data: Validated update payload with optional fields.
            user_id: Owner user ID — verifies ownership.

        Returns:
            The updated media item as a response schema.

        Raises:
            HTTPException: 404 if the item does not exist, 403 if not owner.
        """
        item = await session.get(MediaItem, media_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "media_type" and value is not None:
                setattr(item, field, value.value if hasattr(value, "value") else value)
            elif field == "media_type" and value is None:
                # Skip None media_type — can't unset it
                continue
            else:
                setattr(item, field, value)

        item.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(item)
        return _to_response(item)

    async def delete(
        self, session: AsyncSession, media_id: int, user_id: int = 1
    ) -> None:
        """Delete a media item by ID.

        Args:
            session: The async database session.
            media_id: The item's primary key.
            user_id: Owner user ID — verifies ownership.

        Raises:
            HTTPException: 404 if the item does not exist, 403 if not owner.
        """
        item = await session.get(MediaItem, media_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        await session.delete(item)
        await session.commit()

    # ------------------------------------------------------------------
    # Status, Rating, Tags
    # ------------------------------------------------------------------

    async def update_status(
        self, session: AsyncSession, media_id: int, status: str, user_id: int = 1
    ) -> MediaResponse:
        """Update the consumption status of a media item.

        Automatically sets started_at when transitioning to 'in_progress'
        (only if not already set) and completed_at when transitioning to
        'completed'.

        Args:
            session: The async database session.
            media_id: The item's primary key.
            status: The new status string.
            user_id: Owner user ID — verifies ownership.

        Returns:
            The updated media item.

        Raises:
            HTTPException: 400 for invalid status, 404 if not found, 403 if not owner.
        """
        valid = {s.value for s in MediaStatus}
        if status not in valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Allowed values: pending, in_progress, completed",
            )

        item = await session.get(MediaItem, media_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # No-op: si el estado no cambia, retornar sin modificar timestamps
        if item.status == status:
            return _to_response(item)

        item.status = status
        now = datetime.utcnow()

        if status == MediaStatus.pending.value:
            item.pending_at = now
        elif status == MediaStatus.in_progress.value:
            item.started_at = now
        elif status == MediaStatus.completed.value:
            item.completed_at = now

        item.updated_at = now
        await session.commit()
        await session.refresh(item)
        return _to_response(item)

    async def update_rating(
        self, session: AsyncSession, media_id: int, rating: int, user_id: int = 1
    ) -> MediaResponse:
        """Assign a rating (1-10) to a media item.

        Args:
            session: The async database session.
            media_id: The item's primary key.
            rating: Integer rating between 1 and 10.
            user_id: Owner user ID — verifies ownership.

        Returns:
            The updated media item.

        Raises:
            HTTPException: 400 for invalid rating, 404 if not found, 403 if not owner.
        """
        if not isinstance(rating, int) or rating < 1 or rating > 10:
            raise HTTPException(
                status_code=400,
                detail="Rating must be an integer between 1 and 10",
            )

        item = await session.get(MediaItem, media_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        item.rating = rating
        item.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(item)
        return _to_response(item)

    async def update_tags(
        self, session: AsyncSession, media_id: int, tags: list[str], user_id: int = 1
    ) -> MediaResponse:
        """Replace the tags of a media item.

        Creates any tags that don't already exist in the database.

        Args:
            session: The async database session.
            media_id: The item's primary key.
            tags: List of tag name strings (max 10).
            user_id: Owner user ID — verifies ownership.

        Returns:
            The updated media item.

        Raises:
            HTTPException: 400 if more than 10 tags, 404 if not found, 403 if not owner.
        """
        if len(tags) > 10:
            raise HTTPException(
                status_code=400, detail="Maximum 10 tags per item"
            )

        item = await session.get(MediaItem, media_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        tag_objects = await self._get_or_create_tags(session, tags)
        item.tags = tag_objects
        item.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(item)
        return _to_response(item)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def list_tags(
        self, session: AsyncSession, user_id: int
    ) -> list[str]:
        """Return all unique tag names used by the user's media items.

        Args:
            session: The async database session.
            user_id: Owner user ID.

        Returns:
            Sorted list of unique tag name strings.
        """
        from backend.models.media import media_tags

        query = (
            select(Tag.name)
            .join(media_tags, Tag.id == media_tags.c.tag_id)
            .join(MediaItem, MediaItem.id == media_tags.c.media_id)
            .where(MediaItem.user_id == user_id)
            .distinct()
            .order_by(Tag.name)
        )
        result = await session.execute(query)
        return [row[0] for row in result.all()]

    async def _get_or_create_tags(
        self, session: AsyncSession, tag_names: list[str]
    ) -> list[Tag]:
        """Fetch existing tags or create new ones for the given names.

        Args:
            session: The async database session.
            tag_names: List of tag name strings.

        Returns:
            List of Tag ORM objects.
        """
        tags: list[Tag] = []
        seen: set[str] = set()
        for name in tag_names:
            if name in seen:
                continue
            seen.add(name)
            result = await session.execute(select(Tag).where(Tag.name == name))
            tag = result.scalar_one_or_none()
            if tag is None:
                tag = Tag(name=name)
                session.add(tag)
                await session.flush()
            tags.append(tag)
        return tags
