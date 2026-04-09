"""Social login: users, friendships, friend_requests tables and user_id FK on media_items.

Revision ID: 002_social_login
Revises: 001_initial
Create Date: 2025-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_social_login"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # 2. Insert legacy user for existing media_items
    op.execute(
        "INSERT INTO users (email, username, password_hash) "
        "VALUES ('legacy@personal-shelf.local', 'legacy', 'placeholder')"
    )

    # 3. Add user_id column to media_items, defaulting to the legacy user (id=1)
    op.add_column(
        "media_items",
        sa.Column("user_id", sa.Integer, nullable=True),
    )
    op.execute("UPDATE media_items SET user_id = 1")
    op.alter_column("media_items", "user_id", nullable=False)
    op.create_foreign_key(
        "fk_media_items_user_id",
        "media_items",
        "users",
        ["user_id"],
        ["id"],
    )

    # 4. Create friend_requests table
    op.create_table(
        "friend_requests",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "from_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # 5. Create friendships table (composite PK)
    op.create_table(
        "friendships",
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "friend_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("friendships")
    op.drop_table("friend_requests")
    op.drop_constraint("fk_media_items_user_id", "media_items", type_="foreignkey")
    op.drop_column("media_items", "user_id")
    op.drop_table("users")
