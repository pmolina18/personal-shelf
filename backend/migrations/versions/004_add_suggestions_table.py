"""Add suggestions table.

Revision ID: 004_add_suggestions_table
Revises: 003_add_recommendations_table
Create Date: 2025-01-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_add_suggestions_table"
down_revision: Union[str, None] = "003_add_recommendations_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suggestions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("github_issue_url", sa.String(500), nullable=True),
        sa.Column("github_issue_number", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_suggestions_user_id", "suggestions", ["user_id"])
    op.create_index(
        "ix_suggestions_created_at", "suggestions", [sa.text("created_at DESC")]
    )


def downgrade() -> None:
    op.drop_table("suggestions")
