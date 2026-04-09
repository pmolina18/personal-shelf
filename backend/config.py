"""Application configuration settings."""

import os
from pathlib import Path

# Database
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/media_tracker",
)

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
