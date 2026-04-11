"""Modelo SQLAlchemy para sugerencias de usuarios."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.media import Base

if TYPE_CHECKING:
    from backend.models.user import User


class Suggestion(Base):
    """Representa una sugerencia (feature o bug) enviada por un usuario.

    Attributes:
        id: Identificador único.
        user_id: ID del usuario que creó la sugerencia.
        title: Título de la sugerencia.
        description: Descripción detallada.
        type: Tipo de sugerencia ('feature' o 'bug').
        github_issue_url: URL de la issue creada en GitHub.
        github_issue_number: Número de la issue en GitHub.
        created_at: Timestamp de creación.
        author: Relación con el usuario autor.
    """

    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    github_issue_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_issue_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    author: Mapped["User"] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Suggestion(id={self.id}, title='{self.title}', type='{self.type}')>"
