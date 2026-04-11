"""Servicio de sugerencias — creación y listado."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.suggestion import Suggestion
from backend.models.user import User
from backend.schemas.suggestion import SuggestionCreate, SuggestionList, SuggestionResponse
from backend.services.github_service import GitHubService

logger = logging.getLogger(__name__)


def _to_response(suggestion: Suggestion) -> SuggestionResponse:
    """Convierte un objeto Suggestion ORM a SuggestionResponse.

    Args:
        suggestion: Instancia de Suggestion con relación author cargada.

    Returns:
        SuggestionResponse con los datos formateados.
    """
    return SuggestionResponse(
        id=suggestion.id,
        user_id=suggestion.user_id,
        username=suggestion.author.username,
        title=suggestion.title,
        description=suggestion.description,
        type=suggestion.type,
        github_issue_url=suggestion.github_issue_url,
        github_issue_number=suggestion.github_issue_number,
        created_at=suggestion.created_at,
    )


class SuggestionService:
    """Gestiona la creación y listado de sugerencias."""

    def __init__(self) -> None:
        self._github_service = GitHubService()

    async def create_suggestion(
        self,
        session: AsyncSession,
        user_id: int,
        data: SuggestionCreate,
    ) -> SuggestionResponse:
        """Crea una sugerencia y opcionalmente una issue en GitHub.

        Args:
            session: Sesión async de base de datos.
            user_id: ID del usuario que crea la sugerencia.
            data: Datos de la sugerencia (título, descripción, tipo).

        Returns:
            SuggestionResponse con la sugerencia creada.
        """
        # 1. Crear sugerencia en BD
        suggestion = Suggestion(
            user_id=user_id,
            title=data.title,
            description=data.description,
            type=data.type.value,
        )
        session.add(suggestion)
        await session.flush()

        # 2. Obtener username para el body de la issue
        user = await session.get(User, user_id)
        username = user.username if user else "unknown"

        # 3. Intentar crear issue en GitHub
        label = "bug" if data.type.value == "bug" else "suggestion"
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        body = (
            f"{data.description}\n\n"
            f"---\n"
            f"**Tipo:** {data.type.value}\n"
            f"**Usuario:** {username}\n"
            f"**Fecha:** {now}"
        )
        issue = await self._github_service.create_issue(
            title=data.title,
            body=body,
            labels=[label],
        )

        # 4. Actualizar con datos de GitHub si se creó la issue
        if issue is not None:
            suggestion.github_issue_url = issue["html_url"]
            suggestion.github_issue_number = issue["number"]

        # 5. Commit
        await session.commit()

        # 6. Refrescar para obtener relación author
        await session.refresh(suggestion)

        return _to_response(suggestion)

    async def list_suggestions(
        self,
        session: AsyncSession,
        page: int = 1,
        size: int = 20,
    ) -> SuggestionList:
        """Lista todas las sugerencias con paginación.

        Args:
            session: Sesión async de base de datos.
            page: Número de página (1-indexed).
            size: Cantidad de items por página.

        Returns:
            SuggestionList con items paginados y metadatos.
        """
        query = select(Suggestion)

        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Ordenar y paginar
        query = query.order_by(Suggestion.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await session.execute(query)
        suggestions = result.scalars().unique().all()

        return SuggestionList(
            items=[_to_response(s) for s in suggestions],
            total=total,
            page=page,
            size=size,
        )

    async def list_my_suggestions(
        self,
        session: AsyncSession,
        user_id: int,
        page: int = 1,
        size: int = 20,
    ) -> SuggestionList:
        """Lista las sugerencias del usuario indicado con paginación.

        Args:
            session: Sesión async de base de datos.
            user_id: ID del usuario.
            page: Número de página (1-indexed).
            size: Cantidad de items por página.

        Returns:
            SuggestionList con items paginados y metadatos.
        """
        query = select(Suggestion).where(Suggestion.user_id == user_id)

        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Ordenar y paginar
        query = query.order_by(Suggestion.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await session.execute(query)
        suggestions = result.scalars().unique().all()

        return SuggestionList(
            items=[_to_response(s) for s in suggestions],
            total=total,
            page=page,
            size=size,
        )
