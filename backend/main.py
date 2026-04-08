"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import IMAGE_STORAGE_PATH
from backend.routers.export_import import router as export_import_router
from backend.routers.media import router as media_router
from backend.routers.stats import router as stats_router

app = FastAPI(title="Media Tracker", version="1.0.0")

# CORS – allow the Vue.js frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(media_router)
app.include_router(stats_router)
app.include_router(export_import_router)

# Serve stored images as static files (must be AFTER routers — mounts are catch-all)
app.mount("/images", StaticFiles(directory=str(IMAGE_STORAGE_PATH)), name="images")
