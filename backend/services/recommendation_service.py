"""Servicio de recomendaciones — envío, listado y marcado de lectura."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.media import MediaItem
from backend.models.recommendation import Recommendation
from backend.models.user import User, friendships
from backend.schemas.recommendation import (
    RecommendationCreate,
    RecommendationListResponse,
    RecommendationMediaItem,
    RecommendationResponse,
    RecommendationSender,
)


def _to_response(rec: Recommendation) -> RecommendationResponse:
    """Convierte un objeto Recommendation ORM a RecommendationResponse.

    Args:
        rec: Instancia de Recommendation con relaciones cargadas.

    Returns:
        RecommendationResponse con los datos formateados.
    """
    image_url = rec.media_item.image_path if rec.media_item.image_path else None
    return RecommendationResponse(
        id=rec.id,
        sender=RecommendationSender(
            id=rec.sender.id,
            username=rec.sender.username,
        ),
        receiver=RecommendationSender(
            id=rec.receiver.id,
            username=rec.receiver.username,
        ),
        media_item=RecommendationMediaItem(
            id=rec.media_item.id,
            title=rec.media_item.title,
            media_type=rec.media_item.media_type,
            image_url=image_url,
        ),
        message=rec.message,
        status=rec.status,
        created_at=rec.created_at,
    )


class RecommendationService:
    """Gestiona el envío, listado y marcado de recomendaciones entre amigos."""

    async def send(
        self,
        session: AsyncSession,
        sender_id: int,
        data: RecommendationCreate,
    ) -> RecommendationResponse:
        """Envía una recomendación de media item a un amigo.

        Args:
            session: Sesión async de base de datos.
            sender_id: ID del usuario que envía.
            data: Datos de la recomendación (receiver_id, media_item_id, message).

        Returns:
            RecommendationResponse con la recomendación creada.

        Raises:
            HTTPException: 400 auto-recomendación, 404 usuario/media no encontrado,
                403 no son amigos, 409 duplicado.
        """
        # No auto-recomendación
        if sender_id == data.receiver_id:
            raise HTTPException(
                status_code=400,
                detail="No puedes recomendarte a ti mismo",
            )

        # Verificar que el receiver existe
        receiver = await session.get(User, data.receiver_id)
        if receiver is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Verificar que el media item existe
        media_item = await session.get(MediaItem, data.media_item_id)
        if media_item is None:
            raise HTTPException(status_code=404, detail="Media item no encontrado")

        # Verificar amistad
        friendship_row = await session.execute(
            select(friendships).where(
                friendships.c.user_id == sender_id,
                friendships.c.friend_id == data.receiver_id,
            )
        )
        if friendship_row.first() is None:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes recomendar a amigos confirmados",
            )

        # Verificar duplicado
        existing = await session.execute(
            select(Recommendation).where(
                Recommendation.sender_id == sender_id,
                Recommendation.receiver_id == data.receiver_id,
                Recommendation.media_item_id == data.media_item_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail="Ya recomendaste este item a este usuario",
            )

        # Crear recomendación
        rec = Recommendation(
            sender_id=sender_id,
            receiver_id=data.receiver_id,
            media_item_id=data.media_item_id,
            message=data.message,
            status="pending",
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)

        return _to_response(rec)

    async def list_received(
        self,
        session: AsyncSession,
        user_id: int,
        page: int = 1,
        size: int = 20,
        pending_only: bool = False,
    ) -> RecommendationListResponse:
        """Lista las recomendaciones recibidas por un usuario con paginación.

        Args:
            session: Sesión async de base de datos.
            user_id: ID del usuario receptor.
            page: Número de página (1-indexed).
            size: Cantidad de items por página.
            pending_only: Si True, solo devuelve recomendaciones pendientes.

        Returns:
            RecommendationListResponse con items paginados y metadatos.
        """
        query = select(Recommendation).where(
            Recommendation.receiver_id == user_id
        )

        if pending_only:
            query = query.where(Recommendation.status == "pending")

        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Ordenar y paginar
        query = query.order_by(Recommendation.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        result = await session.execute(query)
        recs = result.scalars().unique().all()

        pages = math.ceil(total / size) if size > 0 else 0

        return RecommendationListResponse(
            items=[_to_response(r) for r in recs],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_unread_count(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> int:
        """Obtiene la cantidad de recomendaciones pendientes de los últimos 7 días.

        Args:
            session: Sesión async de base de datos.
            user_id: ID del usuario receptor.

        Returns:
            Cantidad de recomendaciones pendientes recientes.
        """
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        result = await session.execute(
            select(func.count())
            .select_from(Recommendation)
            .where(
                Recommendation.receiver_id == user_id,
                Recommendation.status == "pending",
                Recommendation.created_at >= one_week_ago,
            )
        )
        return result.scalar() or 0

    async def accept(
        self,
        session: AsyncSession,
        user_id: int,
        recommendation_id: int,
    ) -> RecommendationResponse:
        """Acepta una recomendación: crea el item en el catálogo del receiver como pending.

        Args:
            session: Sesión async de base de datos.
            user_id: ID del usuario autenticado (debe ser el receiver).
            recommendation_id: ID de la recomendación.

        Returns:
            RecommendationResponse con status=accepted.

        Raises:
            HTTPException: 404 si no existe o el usuario no es el receiver.
            HTTPException: 400 si ya fue aceptada o descartada.
        """
        rec = await session.get(Recommendation, recommendation_id)
        if rec is None or rec.receiver_id != user_id:
            raise HTTPException(
                status_code=404, detail="Recomendación no encontrada"
            )

        if rec.status != "pending":
            raise HTTPException(
                status_code=400, detail="Esta recomendación ya fue procesada"
            )

        # Crear el media item en el catálogo del receiver
        source = rec.media_item
        new_item = MediaItem(
            user_id=user_id,
            title=source.title,
            media_type=source.media_type,
            status="pending",
            year=source.year,
            creator=source.creator,
            image_path=source.image_path,
        )
        session.add(new_item)

        rec.status = "accepted"
        await session.commit()
        await session.refresh(rec)

        return _to_response(rec)

    async def dismiss(
        self,
        session: AsyncSession,
        user_id: int,
        recommendation_id: int,
    ) -> RecommendationResponse:
        """Descarta una recomendación sin añadir el item al catálogo.

        Args:
            session: Sesión async de base de datos.
            user_id: ID del usuario autenticado (debe ser el receiver).
            recommendation_id: ID de la recomendación.

        Returns:
            RecommendationResponse con status=dismissed.

        Raises:
            HTTPException: 404 si no existe o el usuario no es el receiver.
            HTTPException: 400 si ya fue aceptada o descartada.
        """
        rec = await session.get(Recommendation, recommendation_id)
        if rec is None or rec.receiver_id != user_id:
            raise HTTPException(
                status_code=404, detail="Recomendación no encontrada"
            )

        if rec.status != "pending":
            raise HTTPException(
                status_code=400, detail="Esta recomendación ya fue procesada"
            )

        rec.status = "dismissed"
        await session.commit()
        await session.refresh(rec)

        return _to_response(rec)
