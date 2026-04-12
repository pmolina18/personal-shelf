"""Replace is_read boolean with status varchar on recommendations.

Revision ID: 005_recommendations_status_column
Revises: 004_add_suggestions_table
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa

revision = "005_rec_status"
down_revision = "004_add_suggestions_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add status column with default
    op.add_column(
        "recommendations",
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
    )

    # 2. Migrate data: is_read=true -> 'accepted', is_read=false -> 'pending'
    op.execute(
        "UPDATE recommendations SET status = 'accepted' WHERE is_read = true"
    )
    op.execute(
        "UPDATE recommendations SET status = 'pending' WHERE is_read = false"
    )

    # 3. Drop old index and column
    op.drop_index("ix_recommendations_receiver_read", table_name="recommendations")
    op.drop_column("recommendations", "is_read")

    # 4. Create new index
    op.create_index(
        "ix_recommendations_receiver_status",
        "recommendations",
        ["receiver_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_recommendations_receiver_status", table_name="recommendations")
    op.add_column(
        "recommendations",
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.execute(
        "UPDATE recommendations SET is_read = true WHERE status = 'accepted'"
    )
    op.execute(
        "UPDATE recommendations SET is_read = false WHERE status != 'accepted'"
    )
    op.drop_column("recommendations", "status")
    op.create_index(
        "ix_recommendations_receiver_read",
        "recommendations",
        ["receiver_id", "is_read"],
    )
