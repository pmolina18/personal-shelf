"""Pydantic schemas for the Explore Catalog feature."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.media import MediaType



class ExploreItem(BaseModel):
    """A deduplicated media item in the global catalog.

    Attributes:
        title: Title of the media item.
        media_type: Type of media (movie, book, series).
        year: Release or publication year.
        creator: Author, director, or creator name.
        image_url: URL to the representative image.
        friends_have: Number of friends who own this title+type.
        friends_recommended: Number of friends who recommended this title+type.
    """

    model_config = ConfigDict(from_attributes=True)

    title: str
    media_type: str
    year: int | None = None
    creator: str | None = None
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    friends_have: int = 0
    friends_recommended: int = 0


class ExploreResult(BaseModel):
    """Paginated response for the global catalog.

    Attributes:
        items: List of deduplicated explore items for the current page.
        total: Total number of deduplicated items matching filters.
        page: Current page number.
        size: Number of items per page.
        pages: Total number of pages.
    """

    items: list[ExploreItem]
    total: int
    page: int
    size: int
    pages: int


class ExploreAddRequest(BaseModel):
    """Request body for adding an explore item to the user's shelf.

    Attributes:
        title: Title of the media item (1-255 chars).
        media_type: Type of media (movie, book, series).
        year: Optional release or publication year.
        creator: Optional author, director, or creator name.
    """

    title: str = Field(..., min_length=1, max_length=255)
    media_type: MediaType
    year: int | None = None
    creator: str | None = Field(None, max_length=255)
