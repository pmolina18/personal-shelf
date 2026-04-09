"""Friend service layer — friend requests, friendships, and user search."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import FriendRequest, User, friendships
from backend.schemas.auth import UserResponse
from backend.schemas.social import FriendRequestResponse, FriendResponse


class FriendService:
    """Handles friend requests, bidirectional friendships, and user search."""

    async def send_request(
        self, session: AsyncSession, from_user_id: int, username: str
    ) -> FriendRequestResponse:
        """Create a pending friend request to the user with the given username.

        Args:
            session: Async database session.
            from_user_id: ID of the user sending the request.
            username: Username of the target user.

        Returns:
            FriendRequestResponse with request details.

        Raises:
            HTTPException: 400 self-request, 404 user not found, 409 duplicate/already friends.
        """
        # Find target user
        result = await session.execute(select(User).where(User.username == username))
        to_user = result.scalar_one_or_none()
        if to_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if to_user.id == from_user_id:
            raise HTTPException(
                status_code=400, detail="Cannot send friend request to yourself"
            )

        # Check if already friends
        row = await session.execute(
            select(friendships).where(
                friendships.c.user_id == from_user_id,
                friendships.c.friend_id == to_user.id,
            )
        )
        if row.first() is not None:
            raise HTTPException(status_code=409, detail="Already friends")

        # Check for existing pending request in either direction
        existing = await session.execute(
            select(FriendRequest).where(
                FriendRequest.status == "pending",
                (
                    (FriendRequest.from_user_id == from_user_id)
                    & (FriendRequest.to_user_id == to_user.id)
                )
                | (
                    (FriendRequest.from_user_id == to_user.id)
                    & (FriendRequest.to_user_id == from_user_id)
                ),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409, detail="Friend request already exists"
            )

        from_user = await session.get(User, from_user_id)

        req = FriendRequest(
            from_user_id=from_user_id,
            to_user_id=to_user.id,
            status="pending",
        )
        session.add(req)
        await session.commit()
        await session.refresh(req)

        return FriendRequestResponse(
            id=req.id,
            from_user=UserResponse(
                id=from_user.id, email=from_user.email, username=from_user.username
            ),
            created_at=req.created_at,
        )

    async def accept_request(
        self, session: AsyncSession, user_id: int, request_id: int
    ) -> dict:
        """Accept a pending friend request and create bidirectional friendship.

        Args:
            session: Async database session.
            user_id: ID of the authenticated user (must be the recipient).
            request_id: ID of the friend request.

        Returns:
            Dict with a success message.

        Raises:
            HTTPException: 404 not found, 403 not recipient.
        """
        req = await session.get(FriendRequest, request_id)
        if req is None or req.status != "pending":
            raise HTTPException(status_code=404, detail="Friend request not found")

        if req.to_user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Insert bidirectional friendship rows
        await session.execute(
            insert(friendships).values(
                user_id=req.from_user_id, friend_id=req.to_user_id
            )
        )
        await session.execute(
            insert(friendships).values(
                user_id=req.to_user_id, friend_id=req.from_user_id
            )
        )

        # Delete the request
        await session.delete(req)
        await session.commit()

        return {"message": "Friend request accepted"}

    async def reject_request(
        self, session: AsyncSession, user_id: int, request_id: int
    ) -> dict:
        """Reject a pending friend request and delete it.

        Args:
            session: Async database session.
            user_id: ID of the authenticated user (must be the recipient).
            request_id: ID of the friend request.

        Returns:
            Dict with a success message.

        Raises:
            HTTPException: 404 not found, 403 not recipient.
        """
        req = await session.get(FriendRequest, request_id)
        if req is None or req.status != "pending":
            raise HTTPException(status_code=404, detail="Friend request not found")

        if req.to_user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        await session.delete(req)
        await session.commit()

        return {"message": "Friend request rejected"}

    async def list_pending(
        self, session: AsyncSession, user_id: int
    ) -> list[FriendRequestResponse]:
        """List pending friend requests received by the user.

        Args:
            session: Async database session.
            user_id: ID of the authenticated user.

        Returns:
            List of FriendRequestResponse for pending incoming requests.
        """
        result = await session.execute(
            select(FriendRequest)
            .where(
                FriendRequest.to_user_id == user_id,
                FriendRequest.status == "pending",
            )
            .order_by(FriendRequest.created_at.desc())
        )
        requests = result.scalars().all()

        responses = []
        for req in requests:
            sender = await session.get(User, req.from_user_id)
            responses.append(
                FriendRequestResponse(
                    id=req.id,
                    from_user=UserResponse(
                        id=sender.id, email=sender.email, username=sender.username
                    ),
                    created_at=req.created_at,
                )
            )
        return responses

    async def list_friends(
        self, session: AsyncSession, user_id: int
    ) -> list[FriendResponse]:
        """List confirmed friends of the user.

        Args:
            session: Async database session.
            user_id: ID of the authenticated user.

        Returns:
            List of FriendResponse with friend id and username.
        """
        result = await session.execute(
            select(User)
            .join(friendships, friendships.c.friend_id == User.id)
            .where(friendships.c.user_id == user_id)
        )
        friends = result.scalars().all()
        return [FriendResponse(id=f.id, username=f.username) for f in friends]

    async def remove_friend(
        self, session: AsyncSession, user_id: int, friend_id: int
    ) -> None:
        """Remove a bidirectional friendship.

        Args:
            session: Async database session.
            user_id: ID of the authenticated user.
            friend_id: ID of the friend to remove.

        Raises:
            HTTPException: 404 if friendship does not exist.
        """
        # Check friendship exists
        row = await session.execute(
            select(friendships).where(
                friendships.c.user_id == user_id,
                friendships.c.friend_id == friend_id,
            )
        )
        if row.first() is None:
            raise HTTPException(status_code=404, detail="Friendship not found")

        # Delete both directions
        await session.execute(
            delete(friendships).where(
                friendships.c.user_id == user_id,
                friendships.c.friend_id == friend_id,
            )
        )
        await session.execute(
            delete(friendships).where(
                friendships.c.user_id == friend_id,
                friendships.c.friend_id == user_id,
            )
        )
        await session.commit()

    async def search_users(
        self, session: AsyncSession, user_id: int, query: str
    ) -> list[FriendResponse]:
        """Search users by username substring, excluding the searcher.

        Args:
            session: Async database session.
            user_id: ID of the authenticated user (excluded from results).
            query: Substring to search for (case-insensitive).

        Returns:
            List of FriendResponse matching the query.
        """
        result = await session.execute(
            select(User).where(
                User.username.ilike(f"%{query}%"),
                User.id != user_id,
            )
        )
        users = result.scalars().all()
        return [FriendResponse(id=u.id, username=u.username) for u in users]
