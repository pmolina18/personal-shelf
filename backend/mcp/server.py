"""MCP server exposing Media Tracker tools for AI assistant interaction.

Each tool delegates to the corresponding service layer method, ensuring
the same validation and business rules as the REST API.

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from backend.db import async_session
from backend.schemas.media import (
    MediaCreate,
    MediaFilters,
    MediaStatus,
    MediaType,
    MediaUpdate,
)
from backend.services.media_service import MediaService
from backend.services.stats_service import StatsService

mcp_server = FastMCP("media-tracker")

_media_service = MediaService()
_stats_service = StatsService()


@mcp_server.tool(
    name="create_media",
    description="Create a new media item in the catalog. "
    "Requires a title and media_type (movie, book, or series). "
    "Optionally accepts year, creator, notes, and tags (max 10).",
)
async def create_media(
    title: str,
    media_type: str,
    year: int | None = None,
    creator: str | None = None,
    notes: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Create a new media item with status 'pending'.

    Args:
        title: Title of the media item (1-255 chars).
        media_type: Type of media: movie, book, or series.
        year: Optional release or publication year.
        creator: Optional author, director, or creator name.
        notes: Optional free-text notes.
        tags: Optional list of tag names (max 10).

    Returns:
        The created media item as a dict.
    """
    try:
        data = MediaCreate(
            title=title,
            media_type=media_type,
            year=year,
            creator=creator,
            notes=notes,
            tags=tags or [],
        )
    except Exception as exc:
        return {"error": str(exc)}

    try:
        async with async_session() as session:
            result = await _media_service.create(session, data, user_id=1)
            return result.model_dump(mode="json")
    except Exception as exc:
        return _format_error(exc)


@mcp_server.tool(
    name="delete_media",
    description="Delete a media item from the catalog by its ID.",
)
async def delete_media(media_id: int) -> dict:
    """Delete a media item by ID.

    Args:
        media_id: The item's primary key.

    Returns:
        Confirmation message or error.
    """
    try:
        async with async_session() as session:
            await _media_service.delete(session, media_id, user_id=1)
            return {"message": f"Media item {media_id} deleted successfully"}
    except Exception as exc:
        return _format_error(exc)


@mcp_server.tool(
    name="update_media",
    description="Update an existing media item. "
    "Only provided fields are modified. "
    "Accepts title, media_type, year, creator, and notes.",
)
async def update_media(
    media_id: int,
    title: str | None = None,
    media_type: str | None = None,
    year: int | None = None,
    creator: str | None = None,
    notes: str | None = None,
) -> dict:
    """Partially update an existing media item.

    Args:
        media_id: The item's primary key.
        title: Updated title (1-255 chars if provided).
        media_type: Updated media type (movie, book, series).
        year: Updated year.
        creator: Updated creator name.
        notes: Updated notes.

    Returns:
        The updated media item as a dict.
    """
    try:
        update_fields: dict = {}
        if title is not None:
            update_fields["title"] = title
        if media_type is not None:
            update_fields["media_type"] = media_type
        if year is not None:
            update_fields["year"] = year
        if creator is not None:
            update_fields["creator"] = creator
        if notes is not None:
            update_fields["notes"] = notes

        data = MediaUpdate(**update_fields)
    except Exception as exc:
        return {"error": str(exc)}

    try:
        async with async_session() as session:
            result = await _media_service.update(session, media_id, data, user_id=1)
            return result.model_dump(mode="json")
    except Exception as exc:
        return _format_error(exc)


@mcp_server.tool(
    name="list_media",
    description="List media items from the catalog with optional filters. "
    "Supports filtering by media_type, status, search text (case-insensitive on title), "
    "and tag. Results are paginated and ordered by creation date descending.",
)
async def list_media(
    media_type: str | None = None,
    status: str | None = None,
    search: str | None = None,
    tag: str | None = None,
    page: int = 1,
    size: int = 20,
) -> dict:
    """Return a paginated, filtered list of media items.

    Args:
        media_type: Filter by type (movie, book, series).
        status: Filter by status (pending, in_progress, completed).
        search: Case-insensitive title search text.
        tag: Filter by tag name.
        page: Page number (1-indexed).
        size: Items per page.

    Returns:
        Paginated result with matching media items.
    """
    try:
        mt = MediaType(media_type) if media_type else None
        st = MediaStatus(status) if status else None
        filters = MediaFilters(media_type=mt, status=st, search=search, tag=tag)
    except Exception as exc:
        return {"error": str(exc)}

    try:
        async with async_session() as session:
            result = await _media_service.list(session, filters, page, size, user_id=1)
            return result.model_dump(mode="json")
    except Exception as exc:
        return _format_error(exc)


@mcp_server.tool(
    name="update_status",
    description="Change the consumption status of a media item. "
    "Valid statuses: pending, in_progress, completed. "
    "Automatically records started_at and completed_at dates.",
)
async def update_status(media_id: int, status: str) -> dict:
    """Update the consumption status of a media item.

    Args:
        media_id: The item's primary key.
        status: New status (pending, in_progress, completed).

    Returns:
        The updated media item as a dict.
    """
    try:
        async with async_session() as session:
            result = await _media_service.update_status(session, media_id, status, user_id=1)
            return result.model_dump(mode="json")
    except Exception as exc:
        return _format_error(exc)


@mcp_server.tool(
    name="rate_media",
    description="Assign a rating (1-10) to a media item.",
)
async def rate_media(media_id: int, rating: int) -> dict:
    """Assign a rating to a media item.

    Args:
        media_id: The item's primary key.
        rating: Integer rating between 1 and 10.

    Returns:
        The updated media item as a dict.
    """
    try:
        async with async_session() as session:
            result = await _media_service.update_rating(session, media_id, rating, user_id=1)
            return result.model_dump(mode="json")
    except Exception as exc:
        return _format_error(exc)


@mcp_server.tool(
    name="manage_tags",
    description="Replace the tags of a media item. "
    "Provide the full list of desired tags (max 10). "
    "Existing tags not in the list will be removed.",
)
async def manage_tags(media_id: int, tags: list[str]) -> dict:
    """Replace the tags of a media item.

    Args:
        media_id: The item's primary key.
        tags: List of tag name strings (max 10).

    Returns:
        The updated media item as a dict.
    """
    try:
        async with async_session() as session:
            result = await _media_service.update_tags(session, media_id, tags, user_id=1)
            return result.model_dump(mode="json")
    except Exception as exc:
        return _format_error(exc)


@mcp_server.tool(
    name="get_stats",
    description="Get catalog statistics: counts by media type, "
    "counts by status, and average rating by media type.",
)
async def get_stats() -> dict:
    """Compute and return catalog statistics.

    Returns:
        Statistics with by_type, by_status, and avg_rating_by_type.
    """
    try:
        async with async_session() as session:
            result = await _stats_service.get_stats(session, user_id=1)
            return result.model_dump(mode="json")
    except Exception as exc:
        return _format_error(exc)


def _format_error(exc: Exception) -> dict:
    """Format an exception into a descriptive error dict.

    Extracts the detail from HTTPException or falls back to str(exc).

    Args:
        exc: The caught exception.

    Returns:
        A dict with an 'error' key containing a descriptive message.
    """
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        return {"error": exc.detail}
    return {"error": f"Internal server error: {exc}"}
