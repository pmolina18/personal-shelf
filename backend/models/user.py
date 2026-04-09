"""SQLAlchemy models for users, friendships, and friend requests."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.media import Base


friendships = Table(
    "friendships",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("friend_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)


class User(Base):
    """Represents a registered user in the application.

    Attributes:
        id: Unique identifier.
        email: User email address (unique).
        username: Display name (unique).
        password_hash: Bcrypt-hashed password.
        created_at: Timestamp when the user was created.
        media_items: Media items owned by this user.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    media_items: Mapped[list["MediaItem"]] = relationship("MediaItem", back_populates="owner")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"


class FriendRequest(Base):
    """Represents a pending friend request between two users.

    Attributes:
        id: Unique identifier.
        from_user_id: ID of the user who sent the request.
        to_user_id: ID of the user who received the request.
        status: Request status (pending, accepted, rejected).
        created_at: Timestamp when the request was created.
        from_user: The sender user relationship.
        to_user: The recipient user relationship.
    """

    __tablename__ = "friend_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    to_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    from_user: Mapped["User"] = relationship("User", foreign_keys=[from_user_id])
    to_user: Mapped["User"] = relationship("User", foreign_keys=[to_user_id])

    def __repr__(self) -> str:
        return f"<FriendRequest(id={self.id}, from={self.from_user_id}, to={self.to_user_id}, status='{self.status}')>"
