"""Pydantic schemas for authentication request/response validation.

Defines models for user registration, login, token management,
and user serialization in API responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """Schema for user registration.

    Attributes:
        email: Valid email address.
        username: Username (3-100 characters).
        password: Password (minimum 8 characters).
    """

    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Schema for user login.

    Attributes:
        identifier: Email address or username.
        password: Account password.
    """

    identifier: str
    password: str


class UserResponse(BaseModel):
    """Schema for serializing a user in API responses.

    Attributes:
        id: Unique user identifier.
        email: User email address.
        username: User display name.
    """

    id: int
    email: str
    username: str


class TokenResponse(BaseModel):
    """Schema for login/register response with tokens and user info.

    Attributes:
        access_token: JWT access token.
        refresh_token: JWT refresh token.
        user: Authenticated user details.
    """

    access_token: str
    refresh_token: str
    user: UserResponse


class RefreshRequest(BaseModel):
    """Schema for token refresh request.

    Attributes:
        refresh_token: Valid JWT refresh token.
    """

    refresh_token: str


class TokenPairResponse(BaseModel):
    """Schema for token refresh response (tokens only, no user).

    Attributes:
        access_token: New JWT access token.
        refresh_token: New JWT refresh token.
    """

    access_token: str
    refresh_token: str


class AccessRequest(BaseModel):
    """Schema for requesting access to the application.

    Attributes:
        email: Valid email address of the requester.
    """

    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")


class AccessRequestResponse(BaseModel):
    """Schema for access request response.

    Attributes:
        message: Confirmation or status message.
        pr_url: URL of the created GitHub Pull Request, if applicable.
    """

    message: str
    pr_url: str | None = None
