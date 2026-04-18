"""Convert image_path from local filenames to external URLs.

Nullifies old local filenames (e.g. movie_abc123.jpg) that are no longer
served since images are now stored as external URLs from TMDB/Open Library.

Revision ID: 007_external_urls
Revises: 006_add_pending_at
Create Date: 2026-04-18
"""

from alembic import op

revision = "007_external_urls"
down_revision = "006_add_pending_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Null out old local filenames that don't start with http
    # New items will have full external URLs (https://image.tmdb.org/... etc.)
    op.execute(
        "UPDATE media_items SET image_path = NULL "
        "WHERE image_path IS NOT NULL AND image_path NOT LIKE 'http%'"
    )


def downgrade() -> None:
    # Cannot restore old local filenames — they were ephemeral anyway
    pass
