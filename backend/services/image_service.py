"""Image service for searching media images from external APIs.

Searches TMDB (movies/series) and Open Library (books) for representative
images and returns their external URLs directly, avoiding local storage
on ephemeral filesystems like Render.
"""

import logging

import httpx

from backend.config import TMDB_API_KEY

logger = logging.getLogger(__name__)


class ImageService:
    """Service for fetching media image URLs from external APIs.

    Returns external URLs directly (e.g. https://image.tmdb.org/...)
    instead of downloading to local storage.
    """

    async def fetch_image(self, title: str, media_type: str) -> str | None:
        """Search for a media image URL from external APIs.

        Tries TMDB for movies/series and Open Library for books. If the
        primary source fails, attempts the other as a fallback.

        Args:
            title: The title of the media item to search for.
            media_type: One of "movie", "book", or "series".

        Returns:
            The external image URL, or None if nothing was found.
        """
        try:
            url = await self._search_image_url(title, media_type)
            if url:
                return url
        except Exception:
            logger.exception("Error fetching image for '%s' (%s)", title, media_type)

        return None

    async def _search_image_url(self, title: str, media_type: str) -> str | None:
        """Search external APIs for an image URL.

        Routes to TMDB for movies/series and Open Library for books,
        with cross-fallback on failure.

        Args:
            title: The media title to search for.
            media_type: One of "movie", "book", or "series".

        Returns:
            An image URL string, or None if nothing was found.
        """
        if media_type == "book":
            url = await self._search_open_library(title)
            if url:
                return url
            return await self._search_tmdb(title, "movie")

        if media_type == "podcast":
            return await self._search_spotify_image(title)

        tmdb_type = "tv" if media_type == "series" else "movie"
        url = await self._search_tmdb(title, tmdb_type)
        if url:
            return url
        return await self._search_open_library(title)

    async def _search_tmdb(self, title: str, tmdb_type: str) -> str | None:
        """Search TMDB for a poster image.

        Args:
            title: The media title to search for.
            tmdb_type: TMDB media type — "movie" or "tv".

        Returns:
            A full image URL, or None if not found or API key is missing.
        """
        if not TMDB_API_KEY:
            logger.debug("TMDB API key not configured, skipping TMDB search")
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.themoviedb.org/3/search/{tmdb_type}",
                    params={"api_key": TMDB_API_KEY, "query": title},
                )
                resp.raise_for_status()
                data = resp.json()

            results = data.get("results", [])
            if not results:
                return None

            poster_path = results[0].get("poster_path")
            if not poster_path:
                return None

            return f"https://image.tmdb.org/t/p/w500{poster_path}"
        except Exception:
            logger.exception("TMDB search failed for '%s'", title)
            return None

    async def _search_open_library(self, title: str) -> str | None:
        """Search Open Library for a book cover image.

        Args:
            title: The book title to search for.

        Returns:
            A cover image URL, or None if not found.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://openlibrary.org/search.json",
                    params={"title": title, "limit": 1},
                )
                resp.raise_for_status()
                data = resp.json()

            docs = data.get("docs", [])
            if not docs:
                return None

            cover_id = docs[0].get("cover_i")
            if not cover_id:
                return None

            return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        except Exception:
            logger.exception("Open Library search failed for '%s'", title)
            return None

    async def _search_spotify_image(self, title: str) -> str | None:
        """Search Spotify for a podcast cover image.

        Args:
            title: The podcast title to search for.

        Returns:
            A cover image URL, or None if not found.
        """
        from backend.services.spotify_auth import get_spotify_token

        token = await get_spotify_token()
        if not token:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"type": "show", "q": title, "limit": 1},
                    headers={"Authorization": f"Bearer {token}"},
                )
                resp.raise_for_status()
                data = resp.json()

            shows = data.get("shows", {}).get("items", [])
            if not shows:
                return None

            images = shows[0].get("images") or []
            return images[0]["url"] if images else None
        except Exception:
            logger.exception("Spotify image search failed for '%s'", title)
            return None
