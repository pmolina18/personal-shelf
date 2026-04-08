# Feature: backend-datetime-image-fix, Property 1: Bug Condition — Imágenes placeholder existen en disco
"""Bug condition exploration test for missing placeholder images.

Validates: Requirements 1.6, 1.7

This test verifies that for each media type (movie, book, series), the
corresponding default placeholder image file exists on disk at the
expected path and has a non-zero file size.

On UNFIXED code this test is EXPECTED TO FAIL because the placeholder
image files (default_movie.png, default_book.png, default_series.png)
do not exist in backend/images/.
"""

from __future__ import annotations

import asyncio

from hypothesis import given, settings
from hypothesis import strategies as st

from backend.config import IMAGE_STORAGE_PATH
from backend.services.image_service import _DEFAULT_IMAGES

# -- Strategies --------------------------------------------------------------

valid_media_types = st.sampled_from(["movie", "book", "series"])


# -- Bug Condition: placeholder images exist on disk -------------------------


@settings(max_examples=10, deadline=None)
@given(media_type=valid_media_types)
def test_placeholder_image_exists_on_disk(media_type: str) -> None:
    """For each media type, the default placeholder image file must exist
    on disk at IMAGE_STORAGE_PATH and have size > 0.

    **Validates: Requirements 1.6, 1.7**
    """

    async def _run() -> None:
        filename = _DEFAULT_IMAGES[media_type]
        filepath = IMAGE_STORAGE_PATH / filename

        assert filepath.exists(), (
            f"Placeholder image '{filename}' for media_type='{media_type}' "
            f"does not exist at {filepath}"
        )
        assert filepath.stat().st_size > 0, (
            f"Placeholder image '{filename}' for media_type='{media_type}' "
            f"exists but has zero size at {filepath}"
        )

    asyncio.run(_run())
