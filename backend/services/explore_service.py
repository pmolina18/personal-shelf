"""Explore service — global catalog with deduplication and social signals."""

from __future__ import annotations

import logging
import math

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.media import MediaItem
from backend.models.recommendation import Recommendation
from backend.models.user import friendships
from backend.schemas.explore import ExploreAddRequest, ExploreItem, ExploreResult
from backend.schemas.media import MediaResponse, MediaStatus
from backend.services.media_service import _to_response

logger = logging.getLogger(__name__)


class ExploreService:
    """Handles the global explore catalog: deduplication, social signals,
    filtering, sorting, and pagination."""

    async def list_global(
        self,
        session: AsyncSession,
        user_id: int,
        media_type: str | None = None,
        search: str | None = None,
        tag: str | None = None,
        sort: str = "title_asc",
        page: int = 1,
        size: int = 20,
    ) -> ExploreResult:
        """Return the deduplicated global catalog with social signals.

        Deduplication groups items by (LOWER(title), media_type) and picks
        a representative preferring items with an image. Social signals
        count how many friends own or recommended each title+type.

        Uses a portable Python-side dedup approach so it works on both
        PostgreSQL and SQLite (tests).

        Args:
            session: Async database session.
            user_id: ID of the authenticated user.
            media_type: Optional filter by media type (exact match).
            search: Optional case-insensitive partial title search.
            sort: Sorting criterion (title_asc, title_desc, friends).
            page: Page number (1-indexed).
            size: Items per page.

        Returns:
            ExploreResult with deduplicated items and pagination metadata.
        """
        # --- 1. Fetch friend IDs (bidirectional via user_id column) ---
        friend_q = select(friendships.c.friend_id).where(
            friendships.c.user_id == user_id
        )
        friend_result = await session.execute(friend_q)
        friend_ids = [row[0] for row in friend_result.fetchall()]

        # --- 2. Build social signal lookup dicts ---
        have_map: dict[tuple[str, str], int] = {}
        rec_map: dict[tuple[str, str], int] = {}

        if friend_ids:
            # friends_have: count distinct friends owning each (lower_title, type)
            have_q = (
                select(
                    func.lower(MediaItem.title).label("lt"),
                    MediaItem.media_type,
                    func.count(func.distinct(MediaItem.user_id)).label("cnt"),
                )
                .where(MediaItem.user_id.in_(friend_ids))
                .group_by(func.lower(MediaItem.title), MediaItem.media_type)
            )
            have_result = await session.execute(have_q)
            for row in have_result.all():
                have_map[(row[0], row[1])] = row[2]

            # friends_recommended: count distinct friends who recommended to user
            rec_q = (
                select(
                    func.lower(MediaItem.title).label("lt"),
                    MediaItem.media_type,
                    func.count(func.distinct(Recommendation.sender_id)).label("cnt"),
                )
                .select_from(Recommendation)
                .join(MediaItem, Recommendation.media_item_id == MediaItem.id)
                .where(
                    Recommendation.receiver_id == user_id,
                    Recommendation.sender_id.in_(friend_ids),
                )
                .group_by(func.lower(MediaItem.title), MediaItem.media_type)
            )
            rec_result = await session.execute(rec_q)
            for row in rec_result.all():
                rec_map[(row[0], row[1])] = row[2]

        # --- 3. Fetch all items (with optional filters) ---
        items_q = select(MediaItem)

        if media_type is not None:
            items_q = items_q.where(MediaItem.media_type == media_type)

        if search:
            items_q = items_q.where(MediaItem.title.ilike(f"%{search}%"))

        # Note: tag filter is applied AFTER deduplication (in Python) to ensure
        # the representative item's tags are checked, not just any duplicate's tags.

        # Order so that items with images come first (for dedup representative)
        items_q = items_q.order_by(
            MediaItem.image_path.is_(None).asc(),
            MediaItem.id.asc(),
        )

        result = await session.execute(items_q)
        all_items = result.scalars().unique().all()

        # --- 4. Deduplicate in Python, excluding user's own items ---
        user_items_q = select(
            func.lower(MediaItem.title),
            MediaItem.media_type,
        ).where(MediaItem.user_id == user_id).distinct()
        user_result = await session.execute(user_items_q)
        user_owned: set[tuple[str, str]] = {(row[0], row[1]) for row in user_result.all()}

        seen: set[tuple[str, str]] = set()
        deduped: list[ExploreItem] = []

        for item in all_items:
            key = (item.title.lower(), item.media_type)
            if key in seen or key in user_owned:
                continue
            seen.add(key)

            fh = have_map.get(key, 0)
            fr = rec_map.get(key, 0)

            deduped.append(
                ExploreItem(
                    title=item.title,
                    media_type=item.media_type,
                    year=item.year,
                    creator=item.creator,
                    image_url=f"/images/{item.image_path}" if item.image_path else None,
                    tags=[t.name for t in item.tags] if item.tags else [],
                    friends_have=fh,
                    friends_recommended=fr,
                )
            )

        # --- 5. Filter by tag (post-dedup) ---
        if tag:
            tag_lower = tag.lower()
            deduped = [
                item for item in deduped
                if any(tag_lower in t.lower() for t in item.tags)
            ]

        # --- 6. Sort ---
        if sort == "title_desc":
            deduped.sort(key=lambda x: x.title.lower(), reverse=True)
        elif sort == "friends":
            deduped.sort(
                key=lambda x: (-(x.friends_have + x.friends_recommended), x.title.lower())
            )
        else:
            # title_asc (default)
            deduped.sort(key=lambda x: x.title.lower())

        # --- 7. Paginate ---
        total = len(deduped)
        pages = math.ceil(total / size) if size > 0 else 0
        start = (page - 1) * size
        end = start + size
        page_items = deduped[start:end]

        return ExploreResult(
            items=page_items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def add_to_shelf(
        self,
        session: AsyncSession,
        user_id: int,
        data: ExploreAddRequest,
    ) -> MediaResponse:
        """Add an explore item to the user's catalog as 'pending'.

        Checks for duplicates by LOWER(title) + media_type before creating.

        Args:
            session: Async database session.
            user_id: ID of the authenticated user.
            data: Validated add-to-shelf payload.

        Returns:
            The created media item as MediaResponse.

        Raises:
            HTTPException: 409 if the user already owns this title+type.
        """
        dup_q = select(MediaItem).where(
            MediaItem.user_id == user_id,
            func.lower(MediaItem.title) == data.title.lower(),
            MediaItem.media_type == data.media_type.value,
        )
        dup_result = await session.execute(dup_q)
        if dup_result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="Ya tienes este item en tu catálogo",
            )

        item = MediaItem(
            user_id=user_id,
            title=data.title,
            media_type=data.media_type.value,
            status=MediaStatus.pending.value,
            year=data.year,
            creator=data.creator,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return _to_response(item)
