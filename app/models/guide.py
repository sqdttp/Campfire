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


class Guide(Record, Base):
    __tablename__ = "guides"
    __table_args__ = (
        UniqueConstraint("platform", "platform_content_id", name="uq_guides_platform_identity"),
        CheckConstraint("view_count >= 0", name="view_count_nonnegative"),
        CheckConstraint("like_count >= 0", name="like_count_nonnegative"),
        CheckConstraint("favorite_count >= 0", name="favorite_count_nonnegative"),
        CheckConstraint("coin_count >= 0", name="coin_count_nonnegative"),
        CheckConstraint("comment_count >= 0", name="comment_count_nonnegative"),
    )
    creator_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("creators.id", ondelete="RESTRICT"), index=True
    )
    platform: Mapped[str] = mapped_column(String(32))
    platform_content_id: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(2048))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    transcript: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    view_count: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    like_count: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    favorite_count: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    coin_count: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    comment_count: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    content_hash: Mapped[str | None] = mapped_column(String(64))
    crawl_status: Mapped[str] = mapped_column(
        String(32), default="pending", server_default="pending"
    )
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="pending", server_default="pending"
    )
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
