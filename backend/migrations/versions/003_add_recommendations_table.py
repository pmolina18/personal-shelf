"""Add recommendations table.

Revision ID: 003_add_recommendations_table
Revises: 002_social_login
Create Date: 2025-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_add_recommendations_table"
down_revision: Union[str, None] = "002_social_login"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "sender_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "receiver_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "media_item_id",
            sa.Integer,
            sa.ForeignKey("media_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column(
            "is_read",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "sender_id",
            "receiver_id",
            "media_item_id",
            name="uq_sender_receiver_media",
        ),
    )

    op.create_index(
        "ix_recommendations_receiver_read",
        "recommendations",
        ["receiver_id", "is_read"],
    )


def downgrade() -> None:
    op.drop_table("recommendations")
