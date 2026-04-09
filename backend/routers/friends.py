"""Friends router — friend requests, friendships, and user search."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.social import (
    FriendRequestCreate,
    FriendRequestResponse,
    FriendResponse,
)
from backend.services.friend_service import FriendService

router = APIRouter(prefix="/api/friends", tags=["friends"])

_friend_service = FriendService()


@router.post("/requests", response_model=FriendRequestResponse, status_code=201)
async def send_request(
    data: FriendRequestCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FriendRequestResponse:
    """Send a friend request to another user.

    Args:
        data: Payload with target username.
        user: Authenticated user.
        session: Async database session.

    Returns:
        The created friend request.
    """
    return await _friend_service.send_request(session, user.id, data.username)


@router.get("/requests/pending", response_model=list[FriendRequestResponse])
async def list_pending(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[FriendRequestResponse]:
    """List pending friend requests received by the authenticated user.

    Args:
        user: Authenticated user.
        session: Async database session.

    Returns:
        List of pending friend requests.
    """
    return await _friend_service.list_pending(session, user.id)


@router.post("/requests/{request_id}/accept")
async def accept_request(
    request_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Accept a pending friend request.

    Args:
        request_id: ID of the friend request.
        user: Authenticated user (must be the recipient).
        session: Async database session.

    Returns:
        Success message.
    """
    return await _friend_service.accept_request(session, user.id, request_id)


@router.post("/requests/{request_id}/reject")
async def reject_request(
    request_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Reject a pending friend request.

    Args:
        request_id: ID of the friend request.
        user: Authenticated user (must be the recipient).
        session: Async database session.

    Returns:
        Success message.
    """
    return await _friend_service.reject_request(session, user.id, request_id)


@router.get("", response_model=list[FriendResponse])
async def list_friends(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[FriendResponse]:
    """List confirmed friends of the authenticated user.

    Args:
        user: Authenticated user.
        session: Async database session.

    Returns:
        List of friends.
    """
    return await _friend_service.list_friends(session, user.id)


@router.delete("/{friend_id}", status_code=204)
async def remove_friend(
    friend_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove a friendship.

    Args:
        friend_id: ID of the friend to remove.
        user: Authenticated user.
        session: Async database session.
    """
    await _friend_service.remove_friend(session, user.id, friend_id)


@router.get("/search", response_model=list[FriendResponse])
async def search_users(
    q: str = Query(..., min_length=1),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[FriendResponse]:
    """Search users by username substring.

    Args:
        q: Search query string.
        user: Authenticated user (excluded from results).
        session: Async database session.

    Returns:
        List of matching users.
    """
    return await _friend_service.search_users(session, user.id, q)
