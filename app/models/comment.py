from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Record


class Comment(Record, Base):
    __tablename__ = "comments"
    __table_args__ = (
        UniqueConstraint("guide_id", "platform_comment_id", name="uq_comments_platform_identity"),
        CheckConstraint("likes >= 0", name="likes_nonnegative"),
        CheckConstraint("reply_count >= 0", name="reply_count_nonnegative"),
    )
    guide_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("guides.id", ondelete="RESTRICT"), index=True
    )
    platform_comment_id: Mapped[str] = mapped_column(String(128))
    parent_comment_id: Mapped[str | None] = mapped_column(String(128))
    user_platform_id: Mapped[str | None] = mapped_column(String(128))
    content: Mapped[str] = mapped_column(Text)
    likes: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    reply_count: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
