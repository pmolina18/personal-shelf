"""Application configuration settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/media_tracker",
)

# CORS — comma-separated origins for production, None allows all in dev
ALLOWED_ORIGINS: str | None = os.getenv("ALLOWED_ORIGINS", None)


def is_neon_db() -> bool:
    """Detect if DATABASE_URL points to a Neon.dev host."""
    return ".neon.tech" in DATABASE_URL


# Image storage
BASE_DIR = Path(__file__).resolve().parent
IMAGE_STORAGE_PATH: Path = BASE_DIR / "images"
IMAGE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# External API keys
TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")

# JWT settings
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super-secret-dev-key-change-in-production")
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# Allowed admins
ALLOWED_ADMINS_PATH: Path = BASE_DIR.parent / "allowed_admins"

# GitHub integration
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO: str = os.getenv("GITHUB_REPO", "")
GITHUB_DEFAULT_BRANCH: str = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
