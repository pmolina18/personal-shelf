"""FastAPI application entry point."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import ALLOWED_ORIGINS
from backend.db import get_session
from backend.routers.admin import router as admin_router
from backend.routers.auth import router as auth_router
from backend.routers.explore import router as explore_router
from backend.routers.feed import router as feed_router
from backend.routers.recommendations import router as recommendations_router
from backend.routers.friends import router as friends_router
from backend.routers.media import router as media_router
from backend.routers.stats import router as stats_router
from backend.routers.suggestions import router as suggestions_router

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
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(media_router)
app.include_router(stats_router)
app.include_router(friends_router)
app.include_router(feed_router)
app.include_router(recommendations_router)
app.include_router(explore_router)
app.include_router(suggestions_router)


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

