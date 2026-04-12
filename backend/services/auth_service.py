"""Authentication service layer with registration, login, and token management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from backend.models.user import User
from backend.schemas.auth import (
    RefreshRequest,
    TokenPairResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from backend.services.allowed_users_service import AllowedUsersService


def _hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password: The plain-text password.

    Returns:
        The bcrypt hash string.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain: The plain-text password.
        hashed: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_access_token(user_id: int) -> str:
    """Create a short-lived JWT access token.

    Args:
        user_id: The user's database ID.

    Returns:
        Encoded JWT access token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _create_refresh_token(user_id: int) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        user_id: The user's database ID.

    Returns:
        Encoded JWT refresh token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


class AuthService:
    """Handles user registration, login, and token refresh."""

    _allowed_users_service = AllowedUsersService()

    async def register(self, session: AsyncSession, data: UserRegister) -> TokenResponse:
        """Register a new user and return tokens.

        Args:
            session: Async database session.
            data: Registration payload with email, username, and password.

        Returns:
            TokenResponse with access_token, refresh_token, and user info.

        Raises:
            HTTPException: 409 if email or username already exists.
        """
        # Verificar que el email está en la lista de usuarios permitidos
        if not self._allowed_users_service.is_allowed(data.email):
            raise HTTPException(
                status_code=403,
                detail="No estás en la lista de usuarios permitidos. Solicita acceso para ser añadido.",
            )

        # Check duplicate email
        result = await session.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="Email already registered")

        # Check duplicate username
        result = await session.execute(select(User).where(User.username == data.username))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="Username already taken")

        user = User(
            email=data.email,
            username=data.username,
            password_hash=_hash_password(data.password),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        access_token = _create_access_token(user.id)
        refresh_token = _create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(id=user.id, email=user.email, username=user.username),
        )

    async def login(self, session: AsyncSession, data: UserLogin) -> TokenResponse:
        """Authenticate a user and return tokens.

        Args:
            session: Async database session.
            data: Login payload with identifier (email or username) and password.

        Returns:
            TokenResponse with access_token, refresh_token, and user info.

        Raises:
            HTTPException: 401 if credentials are invalid (generic message).
        """
        if "@" in data.identifier:
            query = select(User).where(User.email == data.identifier)
        else:
            query = select(User).where(User.username == data.identifier)

        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user is None or not _verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = _create_access_token(user.id)
        refresh_token = _create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(id=user.id, email=user.email, username=user.username),
        )

    async def refresh(self, session: AsyncSession, data: RefreshRequest) -> TokenPairResponse:
        """Validate a refresh token and issue a new token pair.

        Args:
            session: Async database session.
            data: Refresh payload with refresh_token.

        Returns:
            TokenPairResponse with new access_token and refresh_token.

        Raises:
            HTTPException: 401 if the refresh token is invalid or expired.
        """
        try:
            payload = jwt.decode(data.refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        result = await session.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        return TokenPairResponse(
            access_token=_create_access_token(user.id),
            refresh_token=_create_refresh_token(user.id),
        )
