"""Router de recomendaciones — envío, listado y marcado de lectura."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.recommendation import (
    RecommendationCreate,
    RecommendationListResponse,
    RecommendationResponse,
    UnreadCountResponse,
)
from backend.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

_recommendation_service = RecommendationService()


@router.post("", response_model=RecommendationResponse, status_code=201)
async def send_recommendation(
    data: RecommendationCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RecommendationResponse:
    """Envía una recomendación de media item a un amigo.

    Args:
        data: Datos de la recomendación.
        user: Usuario autenticado.
        session: Sesión async de base de datos.

    Returns:
        La recomendación creada.
    """
    return await _recommendation_service.send(session, user.id, data)


@router.get("", response_model=RecommendationListResponse)
async def list_recommendations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    pending_only: bool = Query(False),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RecommendationListResponse:
    """Lista las recomendaciones recibidas por el usuario autenticado."""
    return await _recommendation_service.list_received(
        session, user.id, page, size, pending_only
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UnreadCountResponse:
    """Obtiene la cantidad de recomendaciones no leídas.

    Args:
        user: Usuario autenticado.
        session: Sesión async de base de datos.

    Returns:
        Conteo de recomendaciones no leídas.
    """
    count = await _recommendation_service.get_unread_count(session, user.id)
    return UnreadCountResponse(count=count)


@router.post("/{recommendation_id}/accept", response_model=RecommendationResponse)
async def accept_recommendation(
    recommendation_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RecommendationResponse:
    """Acepta una recomendación y añade el item al catálogo del usuario."""
    return await _recommendation_service.accept(
        session, user.id, recommendation_id
    )


@router.post("/{recommendation_id}/dismiss", response_model=RecommendationResponse)
async def dismiss_recommendation(
    recommendation_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RecommendationResponse:
    """Descarta una recomendación sin añadir el item al catálogo."""
    return await _recommendation_service.dismiss(
        session, user.id, recommendation_id
    )
