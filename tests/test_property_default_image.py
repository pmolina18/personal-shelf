# Feature: media-tracker, Property 14: Image URL from external APIs
"""Property test for image URL fetching (Property 14).

Validates: Requirement 12.5 — images come from external APIs (TMDB, Open Library).
When APIs fail, fetch_image returns None (frontend shows placeholder).
"""

import asyncio
from unittest.mock import AsyncMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

from backend.schemas.media import MediaType
from backend.services.image_service import ImageService

# -- Hypothesis strategies ---------------------------------------------------

valid_media_types = st.sampled_from(
    [MediaType.movie, MediaType.book, MediaType.series]
)

random_titles = st.text(min_size=1, max_size=100).filter(lambda t: t.strip())


# -- Property 14: Image fetch returns None when APIs fail --------------------


@settings(max_examples=100, deadline=None)
@given(
    title=random_titles,
    media_type=valid_media_types,
)
def test_fetch_image_returns_none_when_apis_fail(title, media_type):
    """**Validates: Requirements 12.5**

    For any Media_Item whose ImageService does not find an image from
    external APIs, fetch_image returns None. The frontend handles
    displaying a placeholder based on media_type.
    """

    async def _run():
        svc = ImageService()

        with patch.object(
            svc, "_search_image_url", new_callable=AsyncMock, return_value=None
        ):
            result = await svc.fetch_image(title, media_type.value)

        assert result is None, (
            f"Expected None when APIs fail for {media_type.value}, got '{result}'"
        )

    asyncio.run(_run())


@settings(max_examples=100, deadline=None)
@given(
    title=random_titles,
    media_type=valid_media_types,
)
def test_fetch_image_returns_url_when_api_succeeds(title, media_type):
    """**Validates: Requirements 12.5**

    When an external API returns an image URL, fetch_image passes it
    through directly without downloading.
    """
    fake_url = "https://image.tmdb.org/t/p/w500/test123.jpg"

    async def _run():
        svc = ImageService()

        with patch.object(
            svc, "_search_image_url", new_callable=AsyncMock, return_value=fake_url
        ):
            result = await svc.fetch_image(title, media_type.value)

        assert result == fake_url, (
            f"Expected '{fake_url}', got '{result}'"
        )

    asyncio.run(_run())
