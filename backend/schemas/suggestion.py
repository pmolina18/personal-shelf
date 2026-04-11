"""Schemas Pydantic para sugerencias."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SuggestionType(str, Enum):
    """Tipos de sugerencia permitidos."""

    feature = "feature"
    bug = "bug"


class SuggestionCreate(BaseModel):
    """Schema para crear una nueva sugerencia.

    Attributes:
        title: Título de la sugerencia (1-255 chars).
        description: Descripción detallada (1-2000 chars).
        type: Tipo de sugerencia (feature o bug).
    """

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=2000)
    type: SuggestionType


class SuggestionResponse(BaseModel):
    """Schema de respuesta para una sugerencia.

    Attributes:
        id: Identificador único.
        user_id: ID del usuario autor.
        username: Nombre de usuario del autor.
        title: Título de la sugerencia.
        description: Descripción detallada.
        type: Tipo de sugerencia.
        github_issue_url: URL de la issue en GitHub.
        github_issue_number: Número de la issue en GitHub.
        created_at: Timestamp de creación.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    title: str
    description: str
    type: SuggestionType
    github_issue_url: str | None
    github_issue_number: int | None
    created_at: datetime


class SuggestionList(BaseModel):
    """Schema de respuesta paginada para sugerencias.

    Attributes:
        items: Lista de sugerencias de la página actual.
        total: Total de sugerencias.
        page: Página actual.
        size: Tamaño de página.
    """

    items: list[SuggestionResponse]
    total: int
    page: int
    size: int
