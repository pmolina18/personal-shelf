"""Add pending_at column to media_items.

Revision ID: 006_add_pending_at
Revises: 005_rec_status
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa

revision = "006_add_pending_at"
down_revision = "005_rec_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("media_items", sa.Column("pending_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("media_items", "pending_at")
