# Feature: social-login, Property 1: Round-trip de registro y login
# Feature: social-login, Property 2: Rechazo de registro duplicado
# Feature: social-login, Property 3: Validación de contraseña corta
# Feature: social-login, Property 4: Hashing de contraseña con bcrypt
# Feature: social-login, Property 5: Rechazo de credenciales inválidas
# Feature: social-login, Property 6: Expiración correcta de tokens
# Feature: social-login, Property 7: Identidad del token
# Feature: social-login, Property 8: Endpoints protegidos rechazan sin auth
# Feature: social-login, Property 9: Flujo de refresh token
# Feature: social-login, Property 10: Rechazo de refresh token inválido
"""Property tests for authentication, tokens, and protection (Properties 1-10).

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 4.1, 4.2, 4.3
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from jose import jwt as jose_jwt
from passlib.hash import bcrypt as passlib_bcrypt
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from backend.models.media import Base
from backend.models.user import User  # noqa: F401 — registers users table
from backend.schemas.auth import RefreshRequest, UserLogin, UserRegister
from backend.services.auth_service import AuthService

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# Patch AllowedUsersService.is_allowed to always return True for all property tests
# that call AuthService.register() — the allowed-users gate is tested separately.
_original_is_allowed = None


def _always_allowed(self, email):
    return True


@pytest.fixture(autouse=True)
def _bypass_allowed_users():
    """Bypass the allowed-users check for all auth property tests."""
    from backend.services.allowed_users_service import AllowedUsersService

    original = AllowedUsersService.is_allowed
    AllowedUsersService.is_allowed = _always_allowed
    yield
    AllowedUsersService.is_allowed = original


async def _fresh_session():
    """Create a throwaway in-memory DB and yield a session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()


# -- Hypothesis strategies ---------------------------------------------------

# Emails: simple valid pattern
_valid_emails = st.from_regex(r"[a-z]{3,10}@[a-z]{3,8}\.[a-z]{2,4}", fullmatch=True)

# Usernames: 3-100 chars, alphanumeric
_valid_usernames = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=3,
    max_size=30,
)

# Passwords: 8+ chars, printable
_valid_passwords = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=8,
    max_size=50,
).filter(lambda p: len(p.strip()) >= 8)

# Short passwords: 0-7 chars
_short_passwords = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=0,
    max_size=7,
)


# -- Property 1: Round-trip de registro y login --------------------------------
# **Validates: Requirements 1.1, 2.1**


@settings(max_examples=100, deadline=None)
@given(email=_valid_emails, username=_valid_usernames, password=_valid_passwords)
def test_p1_register_then_login_returns_valid_tokens(email, username, password):
    """For any valid email/username/password, register then login returns valid tokens."""

    async def _run():
        svc = AuthService()
        async for sess in _fresh_session():
            # Register
            reg_data = UserRegister(email=email, username=username, password=password)
            reg_result = await svc.register(sess, reg_data)
            await sess.commit()

            assert reg_result.access_token
            assert reg_result.refresh_token
            assert reg_result.user.email == email
            assert reg_result.user.username == username

            # Login with same credentials
            login_data = UserLogin(email=email, password=password)
            login_result = await svc.login(sess, login_data)

            assert login_result.access_token
            assert login_result.refresh_token
            assert login_result.user.email == email

            # Decode access token to verify it's valid JWT
            payload = jose_jwt.decode(
                login_result.access_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
            )
            assert payload["sub"] == str(login_result.user.id)
            assert payload["type"] == "access"

    asyncio.run(_run())


# -- Property 2: Rechazo de registro duplicado --------------------------------
# **Validates: Requirements 1.2, 1.3**


@settings(max_examples=100, deadline=None)
@given(email=_valid_emails, username=_valid_usernames, password=_valid_passwords)
def test_p2_duplicate_registration_rejected(email, username, password):
    """Registering with existing email or username -> 409, no user count change."""

    async def _run():
        from fastapi import HTTPException

        svc = AuthService()
        async for sess in _fresh_session():
            # Register first user
            reg_data = UserRegister(email=email, username=username, password=password)
            await svc.register(sess, reg_data)
            await sess.commit()

            count_before = (
                await sess.execute(select(func.count(User.id)))
            ).scalar()

            # Try duplicate email
            dup_email = UserRegister(
                email=email, username=username + "x", password=password
            )
            with pytest.raises(HTTPException) as exc_info:
                await svc.register(sess, dup_email)
            assert exc_info.value.status_code == 409

            # Try duplicate username
            dup_user = UserRegister(
                email="other" + email, username=username, password=password
            )
            with pytest.raises(HTTPException) as exc_info:
                await svc.register(sess, dup_user)
            assert exc_info.value.status_code == 409

            count_after = (
                await sess.execute(select(func.count(User.id)))
            ).scalar()
            assert count_before == count_after

    asyncio.run(_run())


# -- Property 3: Validación de contraseña corta --------------------------------
# **Validates: Requirement 1.4**


@settings(max_examples=100, deadline=None)
@given(short_pw=_short_passwords)
def test_p3_short_password_rejected(short_pw):
    """Password of 0-7 chars -> rejection via Pydantic validation, no user created."""

    with pytest.raises(ValidationError):
        UserRegister(email="test@test.com", username="testuser", password=short_pw)


# -- Property 4: Hashing de contraseña con bcrypt -----------------------------
# **Validates: Requirement 1.5**


@settings(max_examples=100, deadline=None)
@given(password=_valid_passwords)
def test_p4_password_hashed_with_bcrypt(password):
    """After registration, password_hash != password and bcrypt.verify(password, hash) == True."""

    async def _run():
        svc = AuthService()
        async for sess in _fresh_session():
            reg_data = UserRegister(
                email="hash@test.com", username="hashuser", password=password
            )
            await svc.register(sess, reg_data)
            await sess.commit()

            result = await sess.execute(select(User).where(User.email == "hash@test.com"))
            user = result.scalar_one()

            assert user.password_hash != password
            assert passlib_bcrypt.verify(password, user.password_hash)

    asyncio.run(_run())


# -- Property 5: Rechazo de credenciales inválidas ----------------------------
# **Validates: Requirement 2.2**


@settings(max_examples=100, deadline=None)
@given(
    email=_valid_emails,
    username=_valid_usernames,
    password=_valid_passwords,
    wrong_password=_valid_passwords,
)
def test_p5_invalid_credentials_rejected(email, username, password, wrong_password):
    """Wrong email or password -> 401 with generic message."""
    assume(password != wrong_password)

    async def _run():
        from fastapi import HTTPException

        svc = AuthService()
        async for sess in _fresh_session():
            # Register
            reg_data = UserRegister(email=email, username=username, password=password)
            await svc.register(sess, reg_data)
            await sess.commit()

            # Wrong password
            with pytest.raises(HTTPException) as exc_info:
                await svc.login(sess, UserLogin(email=email, password=wrong_password))
            assert exc_info.value.status_code == 401
            assert "Invalid credentials" in exc_info.value.detail

            # Non-existent email
            with pytest.raises(HTTPException) as exc_info:
                await svc.login(
                    sess, UserLogin(email="nonexistent@x.com", password=password)
                )
            assert exc_info.value.status_code == 401
            assert "Invalid credentials" in exc_info.value.detail

    asyncio.run(_run())


# -- Property 6: Expiración correcta de tokens --------------------------------
# **Validates: Requirements 2.3, 2.4**


@settings(max_examples=100, deadline=None)
@given(email=_valid_emails, username=_valid_usernames, password=_valid_passwords)
def test_p6_token_expiration_correct(email, username, password):
    """Access token exp ~ 30 min, refresh token exp ~ 7 days from issuance."""

    async def _run():
        svc = AuthService()
        async for sess in _fresh_session():
            now = datetime.now(timezone.utc)
            reg_data = UserRegister(email=email, username=username, password=password)
            result = await svc.register(sess, reg_data)
            await sess.commit()

            # Decode access token
            access_payload = jose_jwt.decode(
                result.access_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
            )
            access_exp = datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
            expected_access = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            assert abs((access_exp - expected_access).total_seconds()) < 60

            # Decode refresh token
            refresh_payload = jose_jwt.decode(
                result.refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
            )
            refresh_exp = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
            expected_refresh = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            assert abs((refresh_exp - expected_refresh).total_seconds()) < 60

    asyncio.run(_run())


# -- Property 7: Identidad del token ------------------------------------------
# **Validates: Requirement 4.3**


@settings(max_examples=100, deadline=None)
@given(email=_valid_emails, username=_valid_usernames, password=_valid_passwords)
def test_p7_token_identity_matches_user(email, username, password):
    """The sub claim of the access token matches the registered user's ID."""

    async def _run():
        svc = AuthService()
        async for sess in _fresh_session():
            reg_data = UserRegister(email=email, username=username, password=password)
            result = await svc.register(sess, reg_data)
            await sess.commit()

            payload = jose_jwt.decode(
                result.access_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
            )
            assert payload["sub"] == str(result.user.id)

            # Verify the user exists in DB with matching data
            db_user = (
                await sess.execute(select(User).where(User.id == int(payload["sub"])))
            ).scalar_one()
            assert db_user.email == email
            assert db_user.username == username

    asyncio.run(_run())


# -- Property 8: Endpoints protegidos rechazan sin auth -----------------------
# **Validates: Requirements 4.1, 4.2**


@settings(max_examples=100, deadline=None)
@given(
    bad_token=st.sampled_from(["", "not-a-jwt", "Bearer.invalid.token", "xyz123"]),
)
def test_p8_protected_endpoints_reject_without_auth(bad_token):
    """Requests without Authorization or with invalid token -> 401.

    Uses a temporary protected endpoint since multi-tenancy guards
    haven't been applied to existing routers yet.
    """
    import httpx
    from fastapi import Depends, FastAPI

    from backend.dependencies import get_current_user

    # Create a minimal app with a protected endpoint
    test_app = FastAPI()

    @test_app.get("/protected")
    async def protected_route(user=Depends(get_current_user)):
        return {"user_id": user.id}

    async def _run():
        transport = httpx.ASGITransport(app=test_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # No auth header
            resp = await client.get("/protected")
            assert resp.status_code in (401, 403)

            # Invalid auth header
            resp = await client.get(
                "/protected", headers={"Authorization": f"Bearer {bad_token}"}
            )
            assert resp.status_code in (401, 403)

    asyncio.run(_run())


# -- Property 9: Flujo de refresh token ---------------------------------------
# **Validates: Requirement 3.1**


@settings(max_examples=100, deadline=None)
@given(email=_valid_emails, username=_valid_usernames, password=_valid_passwords)
def test_p9_refresh_token_flow(email, username, password):
    """Valid refresh token -> new token pair with valid tokens."""

    async def _run():
        svc = AuthService()
        async for sess in _fresh_session():
            # Register to get tokens
            reg_data = UserRegister(email=email, username=username, password=password)
            result = await svc.register(sess, reg_data)
            await sess.commit()

            # Use refresh token
            refresh_data = RefreshRequest(refresh_token=result.refresh_token)
            new_tokens = await svc.refresh(sess, refresh_data)

            assert new_tokens.access_token
            assert new_tokens.refresh_token

            # Verify new access token is valid
            payload = jose_jwt.decode(
                new_tokens.access_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
            )
            assert payload["sub"] == str(result.user.id)
            assert payload["type"] == "access"

            # Verify new refresh token is valid
            ref_payload = jose_jwt.decode(
                new_tokens.refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
            )
            assert ref_payload["type"] == "refresh"

    asyncio.run(_run())


# -- Property 10: Rechazo de refresh token inválido ----------------------------
# **Validates: Requirement 3.2**


@settings(max_examples=100, deadline=None)
@given(
    bad_token=st.one_of(
        st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P")),
            min_size=1,
            max_size=50,
        ),
        st.just("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiwidHlwZSI6InJlZnJlc2giLCJleHAiOjB9.invalid"),
    ),
)
def test_p10_invalid_refresh_token_rejected(bad_token):
    """Non-JWT or expired JWT -> 401."""

    async def _run():
        from fastapi import HTTPException

        svc = AuthService()
        async for sess in _fresh_session():
            with pytest.raises(HTTPException) as exc_info:
                await svc.refresh(sess, RefreshRequest(refresh_token=bad_token))
            assert exc_info.value.status_code == 401

    asyncio.run(_run())
