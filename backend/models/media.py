"""SQLAlchemy models for media_items, tags, and media_tags."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base class for all models."""


media_tags = Table(
    "media_tags",
    Base.metadata,
    Column("media_id", Integer, ForeignKey("media_items.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class MediaItem(Base):
    """Represents a media item (movie, book, or series) in the catalog.

    Attributes:
        id: Unique identifier.
        user_id: ID of the owning user.
        title: Title of the media item.
        media_type: Type of media (movie, book, series).
        status: Consumption status (pending, in_progress, completed).
        rating: User rating from 1 to 10.
        year: Release or publication year.
        creator: Author, director, or creator name.
        notes: Free-text user notes.
        image_path: Path to the stored image file.
        created_at: Timestamp when the item was created.
        updated_at: Timestamp when the item was last updated.
        started_at: Timestamp when consumption started.
        completed_at: Timestamp when consumption was completed.
        tags: Associated tags via many-to-many relationship.
        owner: The user who owns this media item.
    """

    __tablename__ = "media_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    pending_at: Mapped[datetime | None] = mapped_column(nullable=True)

    tags: Mapped[list[Tag]] = relationship(
        "Tag", secondary=media_tags, back_populates="media_items", lazy="selectin"
    )

    owner: Mapped[User] = relationship("User", back_populates="media_items")

    def __repr__(self) -> str:
        return f"<MediaItem(id={self.id}, title='{self.title}', type='{self.media_type}')>"


class Tag(Base):
    """Represents a user-defined tag for classifying media items.

    Attributes:
        id: Unique identifier.
        name: Tag name (unique).
        media_items: Media items associated with this tag.
    """

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    media_items: Mapped[list["MediaItem"]] = relationship(
        "MediaItem", secondary=media_tags, back_populates="tags", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}')>"
