"""Schemas Pydantic para recomendaciones entre amigos."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RecommendationCreate(BaseModel):
    """Schema para enviar una recomendación.

    Attributes:
        receiver_id: ID del usuario destinatario.
        media_item_id: ID del media item a recomendar.
        message: Mensaje opcional (máximo 500 caracteres).
    """

    receiver_id: int
    media_item_id: int
    message: Optional[str] = Field(None, max_length=500)


class RecommendationSender(BaseModel):
    """Sub-schema para representar un usuario en la respuesta.

    Attributes:
        id: ID del usuario.
        username: Nombre de usuario.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class RecommendationMediaItem(BaseModel):
    """Sub-schema para el media item en la respuesta.

    Attributes:
        id: ID del media item.
        title: Título del media item.
        media_type: Tipo de media (movie, book, series).
        image_url: URL de la imagen o None.
    """

    id: int
    title: str
    media_type: str
    image_url: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Schema de respuesta para una recomendación.

    Attributes:
        id: ID de la recomendación.
        sender: Usuario que envió la recomendación.
        receiver: Usuario que recibe la recomendación.
        media_item: Media item recomendado.
        message: Mensaje opcional.
        status: Estado (pending, accepted, dismissed).
        created_at: Fecha de creación.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    sender: RecommendationSender
    receiver: RecommendationSender
    media_item: RecommendationMediaItem
    message: Optional[str]
    status: str
    created_at: datetime


class RecommendationListResponse(BaseModel):
    """Schema de respuesta paginada para listado de recomendaciones.

    Attributes:
        items: Lista de recomendaciones.
        total: Total de recomendaciones.
        page: Página actual.
        size: Tamaño de página.
        pages: Total de páginas.
    """

    items: list[RecommendationResponse]
    total: int
    page: int
    size: int
    pages: int


class UnreadCountResponse(BaseModel):
    """Schema de respuesta para el conteo de no leídas.

    Attributes:
        count: Cantidad de recomendaciones no leídas.
    """

    count: int
