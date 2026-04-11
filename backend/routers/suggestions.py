"""Router de sugerencias — creación y listado."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.suggestion import SuggestionCreate, SuggestionList, SuggestionResponse
from backend.services.suggestion_service import SuggestionService

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])

_suggestion_service = SuggestionService()


@router.post("", response_model=SuggestionResponse, status_code=201)
async def create_suggestion(
    data: SuggestionCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SuggestionResponse:
    """Crea una nueva sugerencia.

    Args:
        data: Datos de la sugerencia.
        user: Usuario autenticado.
        session: Sesión async de base de datos.

    Returns:
        La sugerencia creada.
    """
    return await _suggestion_service.create_suggestion(session, user.id, data)


@router.get("/mine", response_model=SuggestionList)
async def list_my_suggestions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SuggestionList:
    """Lista las sugerencias del usuario autenticado.

    Args:
        page: Número de página.
        size: Tamaño de página.
        user: Usuario autenticado.
        session: Sesión async de base de datos.

    Returns:
        Lista paginada de sugerencias del usuario.
    """
    return await _suggestion_service.list_my_suggestions(session, user.id, page, size)


@router.get("", response_model=SuggestionList)
async def list_suggestions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SuggestionList:
    """Lista todas las sugerencias.

    Args:
        page: Número de página.
        size: Tamaño de página.
        user: Usuario autenticado (requerido para acceso).
        session: Sesión async de base de datos.

    Returns:
        Lista paginada de todas las sugerencias.
    """
    return await _suggestion_service.list_suggestions(session, page, size)
