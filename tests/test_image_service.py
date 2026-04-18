"""Unit tests for ImageService — external URL-based image fetching."""

import pytest

from backend.services.image_service import ImageService


@pytest.fixture
def image_service():
    """Return an ImageService instance."""
    return ImageService()


class TestFetchImage:
    """Tests for fetch_image method."""

    @pytest.mark.asyncio
    async def test_returns_none_when_search_fails(self, image_service, monkeypatch):
        """fetch_image returns None when no external API finds an image."""

        async def _fail_search(self, title, media_type):
            return None

        monkeypatch.setattr(ImageService, "_search_image_url", _fail_search)
        result = await image_service.fetch_image("Nonexistent Movie", "movie")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_url_when_search_succeeds(self, image_service, monkeypatch):
        """fetch_image returns the external URL when search succeeds."""
        expected_url = "https://image.tmdb.org/t/p/w500/abc123.jpg"

        async def _success_search(self, title, media_type):
            return expected_url

        monkeypatch.setattr(ImageService, "_search_image_url", _success_search)
        result = await image_service.fetch_image("Test Movie", "movie")
        assert result == expected_url

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self, image_service, monkeypatch):
        """fetch_image returns None when search raises an exception."""

        async def _raise_search(self, title, media_type):
            raise RuntimeError("API down")

        monkeypatch.setattr(ImageService, "_search_image_url", _raise_search)
        result = await image_service.fetch_image("Test Movie", "movie")
        assert result is None


class TestSearchTmdb:
    """Tests for _search_tmdb method."""

    @pytest.mark.asyncio
    async def test_returns_none_without_api_key(self, image_service, monkeypatch):
        """_search_tmdb returns None when TMDB_API_KEY is empty."""
        monkeypatch.setattr("backend.services.image_service.TMDB_API_KEY", "")
        result = await image_service._search_tmdb("Test", "movie")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_tmdb_url_format(self, image_service, monkeypatch):
        """_search_tmdb returns a URL starting with https://image.tmdb.org."""
        import httpx

        monkeypatch.setattr("backend.services.image_service.TMDB_API_KEY", "fake-key")

        class FakeResponse:
            status_code = 200
            def raise_for_status(self): pass
            def json(self):
                return {"results": [{"poster_path": "/abc123.jpg"}]}

        class FakeClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): pass
            async def get(self, url, **kw): return FakeResponse()

        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: FakeClient())
        result = await image_service._search_tmdb("Test", "movie")
        assert result == "https://image.tmdb.org/t/p/w500/abc123.jpg"
