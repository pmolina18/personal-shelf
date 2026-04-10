"""Modelo SQLAlchemy para recomendaciones entre amigos."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.media import Base

if TYPE_CHECKING:
    from backend.models.media import MediaItem
    from backend.models.user import User


class Recommendation(Base):
    """Representa una recomendación de media item entre dos usuarios.

    Attributes:
        id: Identificador único.
        sender_id: ID del usuario que envía la recomendación.
        receiver_id: ID del usuario que recibe la recomendación.
        media_item_id: ID del media item recomendado.
        message: Mensaje opcional del sender (máximo 500 caracteres).
        status: Estado de la recomendación (pending, accepted, dismissed).
        created_at: Timestamp de creación.
        sender: Relación con el usuario que envía.
        receiver: Relación con el usuario que recibe.
        media_item: Relación con el media item recomendado.
    """

    __tablename__ = "recommendations"
    __table_args__ = (
        UniqueConstraint(
            "sender_id",
            "receiver_id",
            "media_item_id",
            name="uq_sender_receiver_media",
        ),
        Index("ix_recommendations_receiver_status", "receiver_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    receiver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    media_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    sender: Mapped["User"] = relationship(
        "User", foreign_keys=[sender_id], lazy="selectin"
    )
    receiver: Mapped["User"] = relationship(
        "User", foreign_keys=[receiver_id], lazy="selectin"
    )
    media_item: Mapped["MediaItem"] = relationship("MediaItem", lazy="selectin")
