"""Pydantic schemas for Media Tracker request/response validation.

Defines enums for media types and statuses, and Pydantic models for
creating, updating, filtering, and serializing media items. Also includes
schemas for pagination, statistics, and error responses.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MediaType(str, Enum):
    """Allowed media types for catalog items."""

    movie = "movie"
    book = "book"
    series = "series"
    podcast = "podcast"


class MediaStatus(str, Enum):
    """Consumption status of a media item."""

    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class MediaCreate(BaseModel):
    """Schema for creating a new media item.

    Attributes:
        title: Title of the media item (1-255 chars).
        media_type: Type of media (movie, book, series).
        year: Optional release or publication year.
        creator: Optional author, director, or creator name.
        notes: Optional free-text notes.
        tags: List of tag names (max 10).
    """

    title: str = Field(..., min_length=1, max_length=255)
    media_type: MediaType
    year: int | None = None
    creator: str | None = Field(None, max_length=255)
    notes: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=10)


class MediaUpdate(BaseModel):
    """Schema for updating an existing media item.

    All fields are optional; only provided fields are updated.

    Attributes:
        title: Updated title (1-255 chars if provided).
        media_type: Updated media type.
        year: Updated year.
        creator: Updated creator name.
        notes: Updated notes.
    """

    title: str | None = Field(None, min_length=1, max_length=255)
    media_type: MediaType | None = None
    year: int | None = None
    creator: str | None = Field(None, max_length=255)
    notes: str | None = None


class MediaResponse(BaseModel):
    """Schema for serializing a media item in API responses.

    Attributes:
        id: Unique identifier.
        title: Title of the media item.
        media_type: Type of media.
        status: Consumption status.
        rating: User rating (1-10) or None.
        year: Release or publication year.
        creator: Author, director, or creator name.
        notes: Free-text notes.
        image_url: URL to the associated image.
        tags: List of tag names.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        started_at: Consumption start timestamp.
        completed_at: Consumption completion timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    media_type: MediaType
    status: MediaStatus
    rating: int | None
    year: int | None
    creator: str | None
    notes: str | None
    image_url: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    pending_at: datetime | None


class MediaFilters(BaseModel):
    """Schema for filtering media items in list queries.

    Attributes:
        media_type: Filter by media type.
        status: Filter by consumption status.
        search: Case-insensitive title search text.
        tag: Filter by tag name.
    """

    media_type: MediaType | None = None
    status: MediaStatus | None = None
    search: str | None = None
    tag: str | None = None


class PaginatedResult(BaseModel):
    """Schema for paginated list responses.

    Attributes:
        items: List of media items for the current page.
        total: Total number of items matching the query.
        page: Current page number.
        size: Number of items per page.
        pages: Total number of pages.
    """

    items: list[MediaResponse]
    total: int
    page: int
    size: int
    pages: int


class CatalogStats(BaseModel):
    """Schema for catalog statistics.

    Attributes:
        by_type: Count of items grouped by media type.
        by_status: Count of items grouped by status.
        avg_rating_by_type: Average rating grouped by media type.
    """

    by_type: dict[str, int]
    by_status: dict[str, int]
    avg_rating_by_type: dict[str, float | None]


class StatusUpdate(BaseModel):
    """Schema for updating the consumption status of a media item.

    Attributes:
        status: New status value (pending, in_progress, completed).
    """

    status: str = Field(..., min_length=1)


class RatingUpdate(BaseModel):
    """Schema for assigning a rating to a media item.

    Attributes:
        rating: Integer rating between 1 and 10.
    """

    rating: int


class TagsUpdate(BaseModel):
    """Schema for replacing the tags of a media item.

    Attributes:
        tags: List of tag name strings.
    """

    tags: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Schema for API error responses.

    Attributes:
        detail: Human-readable error description.
    """

    detail: str


class MetadataCandidate(BaseModel):
    """Candidato de metadatos devuelto por la búsqueda en APIs externas.

    Attributes:
        title: Título del candidato (obligatorio).
        year: Año de publicación o estreno.
        creator: Director, autor o creador.
        description: Sinopsis o descripción.
        image_url: URL de imagen de portada.
        genres: Lista de géneros o categorías.
    """

    title: str
    year: int | None = None
    creator: str | None = None
    description: str | None = None
    image_url: str | None = None
    genres: list[str] = Field(default_factory=list)
