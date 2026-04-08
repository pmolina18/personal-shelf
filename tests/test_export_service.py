"""Unit tests for ExportService export and import functionality."""

import pytest
from sqlalchemy import select

from backend.models.media import MediaItem
from backend.schemas.media import MediaCreate


@pytest.mark.asyncio
async def test_export_empty_catalog(session, export_service):
    """Exporting an empty catalog returns version, timestamp, and empty items."""
    result = export_service.export_catalog(session)
    data = await result

    assert data["version"] == "1.0"
    assert "exported_at" in data
    assert data["items"] == []


@pytest.mark.asyncio
async def test_export_includes_all_items(session, media_service, export_service):
    """Exported JSON contains every item in the catalog."""
    await media_service.create(
        session, MediaCreate(title="Movie A", media_type="movie")
    )
    await media_service.create(
        session, MediaCreate(title="Book B", media_type="book")
    )

    data = await export_service.export_catalog(session)

    assert len(data["items"]) == 2
    titles = {item["title"] for item in data["items"]}
    assert titles == {"Movie A", "Book B"}


@pytest.mark.asyncio
async def test_export_includes_image_url(session, export_service):
    """Exported items include image_url field (Req 12.6)."""
    item = MediaItem(
        title="With Image",
        media_type="movie",
        status="pending",
        image_path="media/1.jpg",
    )
    session.add(item)
    await session.commit()

    data = await export_service.export_catalog(session)

    assert len(data["items"]) == 1
    assert data["items"][0]["image_url"] == "/images/media/1.jpg"


@pytest.mark.asyncio
async def test_export_includes_tags(session, media_service, export_service):
    """Exported items include their associated tags."""
    await media_service.create(
        session,
        MediaCreate(title="Tagged", media_type="series", tags=["sci-fi", "drama"]),
    )

    data = await export_service.export_catalog(session)

    assert set(data["items"][0]["tags"]) == {"sci-fi", "drama"}


@pytest.mark.asyncio
async def test_import_creates_items(session, export_service):
    """Importing valid JSON creates the corresponding items."""
    data = await export_service.export_catalog(session)
    assert data["items"] == []

    # Build a payload manually
    item = MediaItem(title="Import Me", media_type="book", status="pending")
    session.add(item)
    await session.commit()

    export_data = await export_service.export_catalog(session)

    # Clear the DB
    await session.delete(item)
    await session.commit()

    result = await export_service.import_catalog(session, export_data)

    assert result.created == 1
    assert result.errors == []

    # Verify item exists
    rows = await session.execute(select(MediaItem))
    items = rows.scalars().unique().all()
    assert len(items) == 1
    assert items[0].title == "Import Me"


@pytest.mark.asyncio
async def test_import_preserves_tags(session, media_service, export_service):
    """Imported items retain their tags."""
    await media_service.create(
        session,
        MediaCreate(title="Tagged Item", media_type="movie", tags=["action"]),
    )

    export_data = await export_service.export_catalog(session)

    # Clear DB
    items = (await session.execute(select(MediaItem))).scalars().unique().all()
    for i in items:
        await session.delete(i)
    await session.commit()

    result = await export_service.import_catalog(session, export_data)
    assert result.created == 1

    rows = await session.execute(select(MediaItem))
    imported = rows.scalars().unique().all()
    assert len(imported) == 1
    assert [t.name for t in imported[0].tags] == ["action"]


@pytest.mark.asyncio
async def test_import_invalid_format_raises_400(session, export_service):
    """Importing malformed JSON raises HTTPException 400."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await export_service.import_catalog(session, {"bad": "data"})

    assert exc_info.value.status_code == 400
    assert "Invalid import format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_import_partial_errors(session, export_service):
    """Items that fail individually are recorded as errors without blocking others."""
    payload = {
        "version": "1.0",
        "exported_at": "2025-01-01T00:00:00Z",
        "items": [
            {
                "id": 1,
                "title": "Good Item",
                "media_type": "movie",
                "status": "pending",
                "rating": None,
                "year": None,
                "creator": None,
                "notes": None,
                "image_url": None,
                "tags": [],
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "started_at": None,
                "completed_at": None,
            },
        ],
    }

    result = await export_service.import_catalog(session, payload)
    assert result.created == 1
    assert result.errors == []
