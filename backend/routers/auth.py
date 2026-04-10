"""Authentication router — handles registration, login, and token refresh."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_session
from backend.schemas.auth import (
    AccessRequest,
    AccessRequestResponse,
    RefreshRequest,
    TokenPairResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
)
from backend.services.allowed_users_service import AllowedUsersService
from backend.services.auth_service import AuthService
from backend.services.github_service import GitHubService

router = APIRouter(prefix="/api/auth", tags=["auth"])

_auth_service = AuthService()
_allowed_users_service = AllowedUsersService()
_github_service = GitHubService()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: UserRegister,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Register a new user account.

    Args:
        data: Registration payload with email, username, and password.
        session: Async database session.

    Returns:
        TokenResponse with access and refresh tokens plus user info.
    """
    return await _auth_service.register(session, data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Authenticate with email and password.

    Args:
        data: Login payload with email and password.
        session: Async database session.

    Returns:
        TokenResponse with access and refresh tokens plus user info.
    """
    return await _auth_service.login(session, data)


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenPairResponse:
    """Exchange a valid refresh token for a new token pair.

    Args:
        data: Refresh payload with refresh_token.
        session: Async database session.

    Returns:
        TokenPairResponse with new access and refresh tokens.
    """
    return await _auth_service.refresh(session, data)


@router.post(
    "/request-access",
    response_model=AccessRequestResponse,
    status_code=201,
)
async def request_access(data: AccessRequest) -> AccessRequestResponse:
    """Solicita acceso creando un PR en GitHub.

    Args:
        data: Payload con el email del solicitante.

    Returns:
        AccessRequestResponse con mensaje de confirmación y URL del PR.

    Raises:
        HTTPException: 503 si GitHub no está configurado.
        HTTPException: 409 si el email ya tiene acceso.
        HTTPException: 502 si la API de GitHub falla (propagado desde GitHubService).
    """
    if not _github_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="El servicio de solicitud de acceso no está disponible.",
        )

    if _allowed_users_service.is_allowed(data.email):
        raise HTTPException(
            status_code=409,
            detail="El email ya tiene acceso. Puedes registrarte directamente.",
        )

    pr_info = await _github_service.create_access_request_pr(data.email)

    return AccessRequestResponse(
        message="Solicitud de acceso enviada. Recibirás acceso cuando el propietario apruebe tu solicitud.",
        pr_url=pr_info["html_url"],
    )
