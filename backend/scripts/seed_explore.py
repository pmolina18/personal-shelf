"""Seed script — populates explore catalog with popular content from TMDB and Open Library."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path so `backend` package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx
from sqlalchemy import func, select

from backend.config import TMDB_API_KEY
from backend.db import async_session
from backend.models.media import MediaItem
from backend.models.user import User
from backend.services.image_service import ImageService

logger = logging.getLogger(__name__)

_SYSTEM_EMAIL = "system@personalshelf.app"
_SYSTEM_USERNAME = "system"
_SYSTEM_PASSWORD_HASH = "not-a-real-hash"

_image_service = ImageService()


async def _get_or_create_system_user(session) -> User:
    """Fetch the system user or create one if it doesn't exist.

    Returns:
        The system User instance.
    """
    result = await session.execute(
        select(User).where(User.email == _SYSTEM_EMAIL)
    )
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(
        email=_SYSTEM_EMAIL,
        username=_SYSTEM_USERNAME,
        password_hash=_SYSTEM_PASSWORD_HASH,
    )
    session.add(user)
    await session.flush()
    return user


async def _existing_keys(session, user_id: int) -> set[tuple[str, str]]:
    """Return set of (lower_title, media_type) already owned by the user."""
    q = select(
        func.lower(MediaItem.title), MediaItem.media_type
    ).where(MediaItem.user_id == user_id).distinct()
    result = await session.execute(q)
    return {(row[0], row[1]) for row in result.all()}


async def _fetch_tmdb_movies() -> list[dict]:
    """Fetch top-rated movies from TMDB (pages 1-3, 60 results)."""
    if not TMDB_API_KEY:
        logger.warning("TMDB_API_KEY not set, skipping movies")
        return []
    results = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for page in range(1, 4):
                resp = await client.get(
                    "https://api.themoviedb.org/3/movie/top_rated",
                    params={"api_key": TMDB_API_KEY, "page": page},
                )
                resp.raise_for_status()
                results.extend(resp.json().get("results", []))
    except Exception:
        logger.exception("Failed to fetch TMDB top-rated movies")
    return results


async def _fetch_tmdb_series() -> list[dict]:
    """Fetch top-rated TV series from TMDB (pages 1-3, 60 results)."""
    if not TMDB_API_KEY:
        logger.warning("TMDB_API_KEY not set, skipping series")
        return []
    results = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for page in range(1, 4):
                resp = await client.get(
                    "https://api.themoviedb.org/3/tv/top_rated",
                    params={"api_key": TMDB_API_KEY, "page": page},
                )
                resp.raise_for_status()
                results.extend(resp.json().get("results", []))
    except Exception:
        logger.exception("Failed to fetch TMDB top-rated series")
    return results


async def _fetch_open_library_books() -> list[dict]:
    """Fetch popular books from Open Library (60 results across categories)."""
    categories = ["subject:fiction", "subject:science fiction", "subject:fantasy"]
    all_docs = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for cat in categories:
                resp = await client.get(
                    "https://openlibrary.org/search.json",
                    params={
                        "q": cat,
                        "limit": 20,
                        "fields": "title,first_publish_year,author_name,cover_i",
                    },
                )
                resp.raise_for_status()
                all_docs.extend(resp.json().get("docs", []))
    except Exception:
        logger.exception("Failed to fetch Open Library books")
    return all_docs


async def _seed_tmdb_items(
    session, user_id: int, items: list[dict], media_type: str, existing: set[tuple[str, str]]
) -> int:
    """Create MediaItems from TMDB results, skipping duplicates.

    Args:
        session: Async database session.
        user_id: System user ID.
        items: Raw TMDB result dicts.
        media_type: "movie" or "series".
        existing: Set of already-existing (lower_title, type) keys.

    Returns:
        Number of items created.
    """
    created = 0
    title_key = "title" if media_type == "movie" else "name"
    date_key = "release_date" if media_type == "movie" else "first_air_date"

    for raw in items:
        title = raw.get(title_key) or ""
        if not title:
            continue
        key = (title.lower(), media_type)
        if key in existing:
            continue

        date_str = raw.get(date_key) or ""
        year = int(date_str[:4]) if len(date_str) >= 4 else None

        item = MediaItem(
            user_id=user_id,
            title=title,
            media_type=media_type,
            status="pending",
            year=year,
        )
        session.add(item)
        await session.flush()

        # Fetch poster image
        try:
            image_filename = await _image_service.fetch_image(title, media_type)
            item.image_path = image_filename
        except Exception:
            logger.exception("Image fetch failed for '%s'", title)

        existing.add(key)
        created += 1

    return created


async def _seed_books(
    session, user_id: int, docs: list[dict], existing: set[tuple[str, str]]
) -> int:
    """Create MediaItems from Open Library results, skipping duplicates.

    Args:
        session: Async database session.
        user_id: System user ID.
        docs: Raw Open Library doc dicts.
        existing: Set of already-existing (lower_title, type) keys.

    Returns:
        Number of items created.
    """
    created = 0
    for doc in docs:
        title = doc.get("title") or ""
        if not title:
            continue
        key = (title.lower(), "book")
        if key in existing:
            continue

        year = doc.get("first_publish_year")
        if year is not None:
            year = int(year)

        author_names = doc.get("author_name") or []
        creator = author_names[0] if author_names else None

        item = MediaItem(
            user_id=user_id,
            title=title,
            media_type="book",
            status="pending",
            year=year,
            creator=creator,
        )
        session.add(item)
        await session.flush()

        existing.add(key)
        created += 1

    return created


async def main() -> None:
    """Run the seed process: fetch external data and populate the DB."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    async with async_session() as session:
        user = await _get_or_create_system_user(session)
        existing = await _existing_keys(session, user.id)

        movies_raw, series_raw, books_raw = await asyncio.gather(
            _fetch_tmdb_movies(),
            _fetch_tmdb_series(),
            _fetch_open_library_books(),
        )

        n_movies = await _seed_tmdb_items(session, user.id, movies_raw, "movie", existing)
        n_series = await _seed_tmdb_items(session, user.id, series_raw, "series", existing)
        n_books = await _seed_books(session, user.id, books_raw, existing)

        await session.commit()

    print(f"Created {n_movies} movies, {n_series} series, {n_books} books")


if __name__ == "__main__":
    asyncio.run(main())
