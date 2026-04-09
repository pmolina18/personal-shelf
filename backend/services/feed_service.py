"""Feed service layer — social feed and friend collection viewing."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.media import MediaItem, Tag
from backend.models.user import User, friendships
from backend.schemas.media import MediaFilters, PaginatedResult
from backend.schemas.social import FeedEntry, FeedResponse
from backend.services.media_service import _to_response


class FeedService:
    """Handles the social feed and friend collection viewing."""

    async def get_feed(
        self,
        session: AsyncSession,
        user_id: int,
        page: int = 1,
        size: int = 20,
    ) -> FeedResponse:
        """Return a paginated feed of recent friend activity.

        Scans media_items owned by friends for activity in the last 30 days.
        Actions: "added" (created_at), "completed" (completed_at),
        "rated" (updated_at when rating is not null).

        Args:
            session: Async database session.
            user_id: ID of the authenticated user.
            page: Page number (1-indexed).
            size: Items per page (max 20).

        Returns:
            FeedResponse with feed entries, total, page metadata.
        """
        size = min(size, 20)
        cutoff = datetime.utcnow() - timedelta(days=30)

        # Get friend IDs
        friend_q = select(friendships.c.friend_id).where(
            friendships.c.user_id == user_id
        )
        friend_result = await session.execute(friend_q)
        friend_ids = [row[0] for row in friend_result.fetchall()]

        if not friend_ids:
            return FeedResponse(items=[], total=0, page=page, size=size, pages=0)

        # Fetch friend items with activity in last 30 days
        query = (
            select(MediaItem, User.username)
            .join(User, MediaItem.user_id == User.id)
            .where(MediaItem.user_id.in_(friend_ids))
        )

        result = await session.execute(query)
        rows = result.unique().all()

        # Build feed entries — determine the most recent action per item
        entries: list[FeedEntry] = []
        for item, username in rows:
            action, date = self._determine_action(item)
            if date is None or date < cutoff:
                continue
            entries.append(
                FeedEntry(
                    username=username,
                    title=item.title,
                    media_type=item.media_type,
                    action=action,
                    date=date,
                )
            )

        # Sort by date descending
        entries.sort(key=lambda e: e.date, reverse=True)

        total = len(entries)
        pages = math.ceil(total / size) if size > 0 else 0
        start = (page - 1) * size
        end = start + size
        page_entries = entries[start:end]

        return FeedResponse(
            items=page_entries,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_friend_collection(
        self,
        session: AsyncSession,
        user_id: int,
        friend_id: int,
        filters: MediaFilters,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResult:
        """Return a friend's media collection with filters.

        Verifies friendship before returning results.

        Args:
            session: Async database session.
            user_id: ID of the authenticated user.
            friend_id: ID of the friend whose collection to view.
            filters: Optional filters (media_type, status, search, tag).
            page: Page number (1-indexed).
            size: Items per page.

        Returns:
            PaginatedResult with the friend's items.

        Raises:
            HTTPException: 403 if users are not friends.
        """
        # Verify friendship
        row = await session.execute(
            select(friendships).where(
                friendships.c.user_id == user_id,
                friendships.c.friend_id == friend_id,
            )
        )
        if row.first() is None:
            raise HTTPException(status_code=403, detail="Access denied")

        query = select(MediaItem).where(MediaItem.user_id == friend_id)

        if filters.media_type is not None:
            query = query.where(MediaItem.media_type == filters.media_type.value)

        if filters.status is not None:
            query = query.where(MediaItem.status == filters.status.value)

        if filters.search:
            query = query.where(MediaItem.title.ilike(f"%{filters.search}%"))

        if filters.tag:
            query = query.join(MediaItem.tags).where(Tag.name == filters.tag)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Order and paginate
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

    @staticmethod
    def _determine_action(item: MediaItem) -> tuple[str, datetime | None]:
        """Determine the most recent action and its date for a media item.

        Priority: most recent date among completed_at, updated_at (if rated),
        and created_at.

        Args:
            item: The media item to inspect.

        Returns:
            Tuple of (action_name, action_date).
        """
        candidates: list[tuple[str, datetime]] = []

        if item.created_at is not None:
            candidates.append(("added", item.created_at))

        if item.completed_at is not None:
            candidates.append(("completed", item.completed_at))

        if item.rating is not None and item.updated_at is not None:
            candidates.append(("rated", item.updated_at))

        if not candidates:
            return ("added", None)

        # Return the most recent action
        candidates.sort(key=lambda c: c[1], reverse=True)
        return candidates[0]
