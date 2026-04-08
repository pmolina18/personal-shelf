# Feature: media-tracker, Property 14: Default image based on Media_Type
"""Property test for default image fallback (Property 14).

Validates: Requirement 12.5
"""

import asyncio
from unittest.mock import AsyncMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

from backend.schemas.media import MediaType
from backend.services.image_service import ImageService, _DEFAULT_IMAGES

# -- Hypothesis strategies ---------------------------------------------------

valid_media_types = st.sampled_from(
    [MediaType.movie, MediaType.book, MediaType.series]
)

random_titles = st.text(min_size=1, max_size=100).filter(lambda t: t.strip())


# -- Property 14: Default image based on Media_Type --------------------------


@settings(max_examples=100, deadline=None)
@given(
    title=random_titles,
    media_type=valid_media_types,
)
def test_default_image_assigned_per_media_type(title, media_type):
    """**Validates: Requirements 12.5**

    For any Media_Item whose Image_Service does not find an image, the API
    must assign a default generic image corresponding to the Media_Type of
    the item (a different image for movies, books, and series).
    """

    async def _run():
        svc = ImageService()

        with patch.object(
            svc, "_search_image_url", new_callable=AsyncMock, return_value=None
        ):
            result = await svc.fetch_image(title, media_type.value)

        expected_default = _DEFAULT_IMAGES[media_type.value]
        assert result == expected_default, (
            f"Expected default '{expected_default}' for {media_type.value}, "
            f"got '{result}'"
        )

    asyncio.run(_run())


def test_default_images_are_distinct():
    """**Validates: Requirements 12.5**

    Each media type must receive a distinct default image so that users
    can visually distinguish between movies, books, and series.
    """
    defaults = [_DEFAULT_IMAGES[mt.value] for mt in MediaType]
    assert len(defaults) == len(set(defaults)), (
        f"Default images are not all distinct: {defaults}"
    )
