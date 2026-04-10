"""Backfill script — assigns genre tags to media items that have none.

Queries MetadataService for each untagged item and assigns the first
candidate's genres as tags. Idempotent: skips items that already have tags.

Usage: python -m backend.scripts.backfill_tags
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import async_session
from backend.models.media import MediaItem, Tag
from backend.models.user import User  # noqa: F401 — needed for relationship resolution
from backend.services.metadata_service import MetadataService

logger = logging.getLogger(__name__)
_metadata_service = MetadataService()


async def _get_or_create_tags(session: AsyncSession, tag_names: list[str]) -> list[Tag]:
    """Fetch existing tags or create new ones."""
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


async def main() -> None:
    """Find all items without tags and backfill genres from metadata APIs."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    async with async_session() as session:
        # Find items with no tags
        all_items_q = select(MediaItem).order_by(MediaItem.id)
        result = await session.execute(all_items_q)
        items = result.scalars().unique().all()

        untagged = [i for i in items if not i.tags]
        logger.info("Found %d untagged items out of %d total", len(untagged), len(items))

        tagged_count = 0
        for item in untagged:
            try:
                candidates = await _metadata_service.search(item.title, item.media_type)
                if candidates and candidates[0].genres:
                    genres = candidates[0].genres[:5]
                    tag_objects = await _get_or_create_tags(session, genres)
                    item.tags = tag_objects
                    tagged_count += 1
                    logger.info("Tagged '%s' (%s) with %s", item.title, item.media_type, genres)
                else:
                    logger.info("No genres found for '%s' (%s)", item.title, item.media_type)
            except Exception:
                logger.exception("Failed to tag '%s'", item.title)

        await session.commit()
        print(f"Backfilled tags for {tagged_count}/{len(untagged)} items")


if __name__ == "__main__":
    asyncio.run(main())
