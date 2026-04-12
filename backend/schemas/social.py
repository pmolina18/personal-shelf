"""Pydantic schemas for social features request/response validation.

Defines models for friend requests, friendships, and the social feed.
"""

from datetime import datetime

from pydantic import BaseModel

from backend.schemas.auth import UserResponse


class FriendRequestCreate(BaseModel):
    """Schema for sending a friend request.

    Attributes:
        username: Username of the target user.
    """

    username: str


class FriendRequestResponse(BaseModel):
    """Schema for serializing a pending friend request.

    Attributes:
        id: Unique request identifier.
        from_user: User who sent the request.
        created_at: When the request was created.
    """

    id: int
    from_user: UserResponse
    created_at: datetime


class SentRequestResponse(BaseModel):
    """Schema for serializing a sent friend request (pending).

    Attributes:
        id: Unique request identifier.
        to_user: User who received the request.
        created_at: When the request was created.
    """

    id: int
    to_user: UserResponse
    created_at: datetime


class FriendResponse(BaseModel):
    """Schema for serializing a friend in API responses.

    Attributes:
        id: Friend's user identifier.
        username: Friend's display name.
    """

    id: int
    username: str


class FeedEntry(BaseModel):
    """Schema for a single entry in the social feed.

    Attributes:
        username: Friend's display name.
        title: Media item title.
        media_type: Type of media (movie, book, series).
        action: Action performed (added, completed, rated).
        date: When the action occurred.
    """

    username: str
    title: str
    media_type: str
    action: str
    date: datetime


class FeedResponse(BaseModel):
    """Schema for paginated social feed response.

    Attributes:
        items: List of feed entries for the current page.
        total: Total number of feed entries.
        page: Current page number.
        size: Number of entries per page.
        pages: Total number of pages.
    """

    items: list[FeedEntry]
    total: int
    page: int
    size: int
    pages: int
