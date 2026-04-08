"""Export and import service for catalog JSON serialization."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.media import MediaItem, Tag
from backend.schemas.media import ExportData, ImportResult
from backend.services.media_service import _to_response


class ExportService:
    """Service for exporting and importing the media catalog as JSON.

    Provides methods to serialize the entire catalog to a JSON-compatible
    dict and to import items from a previously exported payload.
    """

    async def export_catalog(self, session: AsyncSession) -> dict:
        """Export all media items as a JSON-serializable dict.

        Queries every MediaItem in the database, converts each to a
        MediaResponse (including image URLs), and wraps them in an
        ExportData envelope with version and timestamp.

        Args:
            session: The async database session.

        Returns:
            A dict matching the ExportData schema with version, exported_at,
            and items list.
        """
        result = await session.execute(select(MediaItem))
        items = result.scalars().unique().all()

        responses = [_to_response(item) for item in items]

        export = ExportData(
            version="1.0",
            exported_at=datetime.now(timezone.utc),
            items=responses,
        )
        return export.model_dump(mode="json")

    async def import_catalog(
        self, session: AsyncSession, data: dict
    ) -> ImportResult:
        """Import media items from a JSON payload.

        Validates the incoming dict against the ExportData schema, then
        creates a new MediaItem for each entry. Tags are reused when they
        already exist. Individual item failures are recorded as errors
        without aborting the entire import.

        Args:
            session: The async database session.
            data: A dict matching the ExportData schema.

        Returns:
            An ImportResult with the count of created items and any errors.

        Raises:
            HTTPException: 400 if the top-level JSON structure is invalid.
        """
        try:
            export_data = ExportData(**data)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid import format: {exc}",
            )

        created = 0
        errors: list[str] = []

        for idx, item_data in enumerate(export_data.items):
            try:
                item = MediaItem(
                    title=item_data.title,
                    media_type=item_data.media_type.value,
                    status=item_data.status.value,
                    rating=item_data.rating,
                    year=item_data.year,
                    creator=item_data.creator,
                    notes=item_data.notes,
                    started_at=item_data.started_at,
                    completed_at=item_data.completed_at,
                )

                if item_data.tags:
                    tags = await self._get_or_create_tags(session, item_data.tags)
                    item.tags = tags

                session.add(item)
                await session.flush()
                created += 1
            except Exception as exc:
                errors.append(f"Item {idx} ('{item_data.title}'): {exc}")

        await session.commit()
        return ImportResult(created=created, errors=errors)

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
