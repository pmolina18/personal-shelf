"""Pydantic schemas for admin dashboard statistics.

Defines models for the GET /api/admin/stats response, including
user metrics, content metrics, social metrics, rankings, and
recent activity.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TypeDistribution(BaseModel):
    """Distribución de MediaItems por media_type."""

    movie: int
    book: int
    series: int


class StatusDistribution(BaseModel):
    """Distribución de MediaItems por status."""

    pending: int
    in_progress: int
    completed: int


class TopUser(BaseModel):
    """Usuario en el ranking de más activos."""

    username: str
    count: int


class TopTag(BaseModel):
    """Tag en el ranking de más utilizados."""

    name: str
    count: int


class RecentActivity(BaseModel):
    """Acción reciente en la aplicación."""

    title: str
    media_type: str
    username: str
    timestamp: datetime


class UserMetrics(BaseModel):
    """Métricas de usuarios."""

    total: int
    new_this_week: int
    active_this_week: int


class ContentMetrics(BaseModel):
    """Métricas de contenido."""

    total: int
    new_this_week: int
    by_type: TypeDistribution
    by_status: StatusDistribution
    avg_rating: float | None


class SocialMetrics(BaseModel):
    """Métricas sociales."""

    total_friendships: int
    pending_requests: int
    unique_tags: int


class AdminStatsResponse(BaseModel):
    """Respuesta completa del endpoint GET /api/admin/stats."""

    users: UserMetrics
    content: ContentMetrics
    social: SocialMetrics
    top_users: list[TopUser]
    top_tags: list[TopTag]
    recent_activity: list[RecentActivity]
