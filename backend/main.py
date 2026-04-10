"""FastAPI application entry point."""

import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import ALLOWED_ORIGINS, IMAGE_STORAGE_PATH, TMDB_API_KEY
from backend.db import get_session
from backend.models.media import MediaItem
from backend.routers.auth import router as auth_router
from backend.routers.explore import router as explore_router
from backend.routers.feed import router as feed_router
from backend.routers.recommendations import router as recommendations_router
from backend.routers.friends import router as friends_router
from backend.routers.media import router as media_router
from backend.routers.stats import router as stats_router
from backend.services.image_service import ImageService

app = FastAPI(title="Media Tracker", version="1.0.0")

# CORS – configurable origins for production, permissive for local dev
origins = ALLOWED_ORIGINS.split(",") if ALLOWED_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Register API routers
app.include_router(auth_router)
app.include_router(media_router)
app.include_router(stats_router)
app.include_router(friends_router)
app.include_router(feed_router)
app.include_router(recommendations_router)
app.include_router(explore_router)


@app.get("/api/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    """Check backend and database health for Render monitoring."""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "detail": "database connection failed"},
        )


logger = logging.getLogger(__name__)
_image_service = ImageService()


@app.get("/images/{filename}")
async def serve_image(
    filename: str,
    session: AsyncSession = Depends(get_session),
):
    """Serve a stored image, attempting re-download if missing.

    When the requested file doesn't exist on disk and TMDB_API_KEY is
    configured, looks up the media item that owns this image and tries
    to re-download it from external APIs before returning 404.

    Args:
        filename: Image filename (e.g. "movie_abc123.jpg").
        session: Async database session.

    Returns:
        FileResponse with the image, or 404 JSON if not found.
    """
    filepath = IMAGE_STORAGE_PATH / filename

    if filepath.is_file():
        return FileResponse(filepath)

    # File missing — attempt re-download if TMDB key is available
    if TMDB_API_KEY:
        stmt = select(MediaItem).where(MediaItem.image_path == filename).limit(1)
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()

        if item is not None:
            new_filename = await _image_service.fetch_image(
                item.title, item.media_type,
            )
            new_path = IMAGE_STORAGE_PATH / new_filename
            if new_path.is_file() and new_filename == filename:
                return FileResponse(new_path)

    raise HTTPException(status_code=404, detail="Image not found")
