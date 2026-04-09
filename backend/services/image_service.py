"""Image service for searching, downloading, and storing media images.

Searches external APIs (TMDB for movies/series, Open Library for books)
for representative images, downloads them to local storage, and provides
fallback default images when no result is found or an error occurs.
"""

import hashlib
import logging

import httpx

from backend.config import IMAGE_STORAGE_PATH, TMDB_API_KEY

logger = logging.getLogger(__name__)

# Default image filenames per media type
_DEFAULT_IMAGES: dict[str, str] = {
    "movie": "default_movie.png",
    "book": "default_book.png",
    "series": "default_series.png",
}


class ImageService:
    """Service for fetching and storing media images.

    Searches external APIs by title and media type, downloads the best
    match, and stores it locally. Falls back to a default image when
    the search fails or no results are found.
    """

    async def fetch_image(self, title: str, media_type: str) -> str:
        """Search for a media image and store it locally.

        Tries TMDB for movies/series and Open Library for books. If the
        primary source fails, attempts the other as a fallback. On any
        failure, returns a default image path.

        Args:
            title: The title of the media item to search for.
            media_type: One of "movie", "book", or "series".

        Returns:
            The filename of the stored image (relative to IMAGE_STORAGE_PATH).
        """
        try:
            image_url = await self._search_image_url(title, media_type)
            if image_url:
                local_path = await self._download_and_store(image_url, title, media_type)
                if local_path:
                    return local_path
        except Exception:
            logger.exception("Error fetching image for '%s' (%s)", title, media_type)

        return await self.get_default_image(media_type)

    async def get_default_image(self, media_type: str) -> str:
        """Return the default image filename for a given media type.

        Args:
            media_type: One of "movie", "book", or "series".

        Returns:
            The default image filename for the media type.
        """
        return _DEFAULT_IMAGES.get(media_type, _DEFAULT_IMAGES["movie"])

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

    async def _download_and_store(
        self, image_url: str, title: str, media_type: str
    ) -> str | None:
        """Download an image from a URL and store it locally.

        The filename is derived from a hash of the title and media type
        to ensure uniqueness and avoid filesystem issues with special
        characters.

        Args:
            image_url: The URL to download the image from.
            title: The media title (used for filename generation).
            media_type: The media type (used for filename generation).

        Returns:
            The stored filename, or None if the download failed.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(image_url)
                resp.raise_for_status()
                content = resp.content

            if not content:
                return None

            # Determine extension from content type or URL
            ext = self._guess_extension(resp.headers.get("content-type", ""), image_url)

            # Generate a stable filename from title + media_type
            name_hash = hashlib.md5(
                f"{title}:{media_type}".encode()
            ).hexdigest()[:12]
            filename = f"{media_type}_{name_hash}{ext}"

            filepath = IMAGE_STORAGE_PATH / filename
            filepath.write_bytes(content)

            logger.info("Stored image for '%s' (%s) at %s", title, media_type, filepath)
            return filename
        except Exception:
            logger.exception("Failed to download image from %s", image_url)
            return None

    @staticmethod
    def _guess_extension(content_type: str, url: str) -> str:
        """Guess the file extension from content type or URL.

        Args:
            content_type: The HTTP Content-Type header value.
            url: The image URL.

        Returns:
            A file extension string including the dot (e.g. ".jpg").
        """
        ct_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        for ct, ext in ct_map.items():
            if ct in content_type:
                return ext

        # Fall back to URL extension
        url_lower = url.lower()
        for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            if ext in url_lower:
                return ext if ext != ".jpeg" else ".jpg"

        return ".jpg"
