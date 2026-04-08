"""Unit tests for ImageService."""

import pytest

from backend.services.image_service import ImageService, _DEFAULT_IMAGES


@pytest.fixture
def image_service():
    """Return an ImageService instance."""
    return ImageService()


class TestGetDefaultImage:
    """Tests for get_default_image method."""

    @pytest.mark.asyncio
    async def test_returns_movie_default(self, image_service):
        result = await image_service.get_default_image("movie")
        assert result == "default_movie.png"

    @pytest.mark.asyncio
    async def test_returns_book_default(self, image_service):
        result = await image_service.get_default_image("book")
        assert result == "default_book.png"

    @pytest.mark.asyncio
    async def test_returns_series_default(self, image_service):
        result = await image_service.get_default_image("series")
        assert result == "default_series.png"

    @pytest.mark.asyncio
    async def test_unknown_type_falls_back_to_movie(self, image_service):
        result = await image_service.get_default_image("unknown")
        assert result == "default_movie.png"

    @pytest.mark.asyncio
    async def test_each_media_type_has_distinct_default(self):
        defaults = set(_DEFAULT_IMAGES.values())
        assert len(defaults) == 3, "Each media type must have a distinct default image"


class TestGuessExtension:
    """Tests for _guess_extension static method."""

    def test_jpeg_content_type(self):
        assert ImageService._guess_extension("image/jpeg", "") == ".jpg"

    def test_png_content_type(self):
        assert ImageService._guess_extension("image/png", "") == ".png"

    def test_falls_back_to_url(self):
        assert ImageService._guess_extension("application/octet-stream", "http://example.com/img.png") == ".png"

    def test_defaults_to_jpg(self):
        assert ImageService._guess_extension("", "http://example.com/image") == ".jpg"


class TestFetchImageFallback:
    """Tests that fetch_image falls back to default on errors."""

    @pytest.mark.asyncio
    async def test_returns_default_when_no_api_keys(self, image_service, monkeypatch):
        monkeypatch.setattr("backend.config.TMDB_API_KEY", "")

        async def _fail_search(self, title, media_type):
            return None

        monkeypatch.setattr(ImageService, "_search_image_url", _fail_search)
        result = await image_service.fetch_image("Nonexistent Movie 12345xyz", "movie")
        assert result == "default_movie.png"

    @pytest.mark.asyncio
    async def test_returns_default_for_book_when_apis_fail(self, image_service, monkeypatch):
        async def _fail_search(self, title, media_type):
            return None

        monkeypatch.setattr(ImageService, "_search_image_url", _fail_search)
        result = await image_service.fetch_image("Some Book", "book")
        assert result == "default_book.png"

    @pytest.mark.asyncio
    async def test_returns_default_for_series_when_apis_fail(self, image_service, monkeypatch):
        async def _fail_search(self, title, media_type):
            return None

        monkeypatch.setattr(ImageService, "_search_image_url", _fail_search)
        result = await image_service.fetch_image("Some Series", "series")
        assert result == "default_series.png"
