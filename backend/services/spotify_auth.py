"""Spotify Client Credentials token management.

Provides a module-level cached token for Spotify Web API access.
Both MetadataService and ImageService import get_spotify_token()
to avoid duplicating auth logic.
"""

from __future__ import annotations

import base64
import logging
import time

import httpx

from backend.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

logger = logging.getLogger(__name__)

_token: str | None = None
_expires_at: float = 0


async def get_spotify_token() -> str | None:
    """Return a valid Spotify access token, or None if credentials are missing.

    Uses the Client Credentials flow. Caches the token in module-level
    variables and renews it when it's within 60 seconds of expiry.

    Returns:
        A valid Bearer token string, or None.
    """
    global _token, _expires_at

    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        logger.debug("Spotify credentials not configured, skipping")
        return None

    # Return cached token if still valid (with 60s safety margin)
    if _token and time.time() < _expires_at - 60:
        return _token

    try:
        credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://accounts.spotify.com/api/token",
                headers={
                    "Authorization": f"Basic {encoded}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )
            resp.raise_for_status()
            data = resp.json()

        _token = data["access_token"]
        _expires_at = time.time() + data.get("expires_in", 3600)
        logger.info("Spotify token obtained, expires in %ds", data.get("expires_in", 3600))
        return _token
    except Exception:
        logger.exception("Failed to obtain Spotify access token")
        _token = None
        _expires_at = 0
        return None
