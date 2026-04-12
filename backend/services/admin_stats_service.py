"""Service for computing global admin dashboard statistics."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.media import MediaItem, Tag, media_tags
from backend.models.user import FriendRequest, User, friendships
from backend.schemas.admin import (
    AdminStatsResponse,
    ContentMetrics,
    RecentActivity,
    SocialMetrics,
    StatusDistribution,
    TopTag,
    TopUser,
    TypeDistribution,
    UserMetrics,
)


class AdminStatsService:
    """Service for computing global application statistics for the admin dashboard."""

    async def get_admin_stats(self, session: AsyncSession) -> AdminStatsResponse:
        """Compute global admin statistics across all users.

        Gathers user metrics, content metrics, social metrics,
        top user/tag rankings, and recent activity.

        Args:
            session: The async database session.

        Returns:
            An AdminStatsResponse with all aggregated statistics.
        """
        one_week_ago = datetime.utcnow() - timedelta(days=7)

        user_metrics = await self._get_user_metrics(session, one_week_ago)
        content_metrics = await self._get_content_metrics(session, one_week_ago)
        social_metrics = await self._get_social_metrics(session)
        top_users = await self._get_top_users(session, one_week_ago)
        top_tags = await self._get_top_tags(session)
        recent_activity = await self._get_recent_activity(session)

        return AdminStatsResponse(
            users=user_metrics,
            content=content_metrics,
            social=social_metrics,
            top_users=top_users,
            top_tags=top_tags,
            recent_activity=recent_activity,
        )

    async def _get_user_metrics(
        self, session: AsyncSession, one_week_ago: datetime
    ) -> UserMetrics:
        """Compute user metrics: total, new this week, active this week.

        Args:
            session: The async database session.
            one_week_ago: Cutoff datetime for "this week" calculations.

        Returns:
            A UserMetrics instance.
        """
        # Total users
        total_result = await session.execute(select(func.count(User.id)))
        total = total_result.scalar_one()

        # New users in last 7 days
        new_result = await session.execute(
            select(func.count(User.id)).where(User.created_at >= one_week_ago)
        )
        new_this_week = new_result.scalar_one()

        # Active users: distinct user_ids with MediaItems created in last 7 days
        active_result = await session.execute(
            select(func.count(func.distinct(MediaItem.user_id))).where(
                MediaItem.created_at >= one_week_ago
            )
        )
        active_this_week = active_result.scalar_one()

        return UserMetrics(
            total=total,
            new_this_week=new_this_week,
            active_this_week=active_this_week,
        )

    async def _get_content_metrics(
        self, session: AsyncSession, one_week_ago: datetime
    ) -> ContentMetrics:
        """Compute content metrics: total, new, by type/status, avg rating.

        Args:
            session: The async database session.
            one_week_ago: Cutoff datetime for "this week" calculations.

        Returns:
            A ContentMetrics instance.
        """
        # Total MediaItems
        total_result = await session.execute(select(func.count(MediaItem.id)))
        total = total_result.scalar_one()

        # New MediaItems in last 7 days
        new_result = await session.execute(
            select(func.count(MediaItem.id)).where(
                MediaItem.created_at >= one_week_ago
            )
        )
        new_this_week = new_result.scalar_one()

        # Distribution by media_type
        type_result = await session.execute(
            select(MediaItem.media_type, func.count()).group_by(MediaItem.media_type)
        )
        type_raw = {row[0]: row[1] for row in type_result.all()}
        by_type = TypeDistribution(
            movie=type_raw.get("movie", 0),
            book=type_raw.get("book", 0),
            series=type_raw.get("series", 0),
        )

        # Distribution by status
        status_result = await session.execute(
            select(MediaItem.status, func.count()).group_by(MediaItem.status)
        )
        status_raw = {row[0]: row[1] for row in status_result.all()}
        by_status = StatusDistribution(
            pending=status_raw.get("pending", 0),
            in_progress=status_raw.get("in_progress", 0),
            completed=status_raw.get("completed", 0),
        )

        # Global average rating (only items with rating)
        avg_result = await session.execute(
            select(func.avg(MediaItem.rating)).where(MediaItem.rating.isnot(None))
        )
        avg_raw = avg_result.scalar_one()
        avg_rating = float(avg_raw) if avg_raw is not None else None

        return ContentMetrics(
            total=total,
            new_this_week=new_this_week,
            by_type=by_type,
            by_status=by_status,
            avg_rating=avg_rating,
        )

    async def _get_social_metrics(self, session: AsyncSession) -> SocialMetrics:
        """Compute social metrics: friendships, pending requests, unique tags.

        Args:
            session: The async database session.

        Returns:
            A SocialMetrics instance.
        """
        # Total friendships (rows / 2 since bidirectional)
        friendship_result = await session.execute(
            select(func.count()).select_from(friendships)
        )
        total_rows = friendship_result.scalar_one()
        total_friendships = total_rows // 2

        # Pending friend requests
        pending_result = await session.execute(
            select(func.count(FriendRequest.id)).where(
                FriendRequest.status == "pending"
            )
        )
        pending_requests = pending_result.scalar_one()

        # Unique tags
        tags_result = await session.execute(select(func.count(Tag.id)))
        unique_tags = tags_result.scalar_one()

        return SocialMetrics(
            total_friendships=total_friendships,
            pending_requests=pending_requests,
            unique_tags=unique_tags,
        )

    async def _get_top_users(
        self, session: AsyncSession, one_week_ago: datetime
    ) -> list[TopUser]:
        """Get top 5 users by MediaItems created in the last 7 days.

        Args:
            session: The async database session.
            one_week_ago: Cutoff datetime for the ranking period.

        Returns:
            A list of up to 5 TopUser entries, ordered by count descending.
        """
        result = await session.execute(
            select(User.username, func.count(MediaItem.id).label("cnt"))
            .join(MediaItem, MediaItem.user_id == User.id)
            .where(MediaItem.created_at >= one_week_ago)
            .group_by(User.username)
            .order_by(func.count(MediaItem.id).desc())
            .limit(5)
        )
        return [TopUser(username=row[0], count=row[1]) for row in result.all()]

    async def _get_top_tags(self, session: AsyncSession) -> list[TopTag]:
        """Get top 5 tags by number of associated MediaItems.

        Args:
            session: The async database session.

        Returns:
            A list of up to 5 TopTag entries, ordered by count descending.
        """
        result = await session.execute(
            select(Tag.name, func.count(media_tags.c.media_id).label("cnt"))
            .join(media_tags, Tag.id == media_tags.c.tag_id)
            .group_by(Tag.name)
            .order_by(func.count(media_tags.c.media_id).desc())
            .limit(5)
        )
        return [TopTag(name=row[0], count=row[1]) for row in result.all()]

    async def _get_recent_activity(
        self, session: AsyncSession
    ) -> list[RecentActivity]:
        """Get the 10 most recently updated MediaItems.

        Args:
            session: The async database session.

        Returns:
            A list of up to 10 RecentActivity entries, ordered by updated_at desc.
        """
        result = await session.execute(
            select(
                MediaItem.title,
                MediaItem.media_type,
                User.username,
                MediaItem.updated_at,
            )
            .join(User, MediaItem.user_id == User.id)
            .order_by(MediaItem.updated_at.desc())
            .limit(10)
        )
        return [
            RecentActivity(
                title=row[0],
                media_type=row[1],
                username=row[2],
                timestamp=row[3],
            )
            for row in result.all()
        ]
