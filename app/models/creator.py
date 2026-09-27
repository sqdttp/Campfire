from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Record


class Creator(Record, Base):
    __tablename__ = "creators"
    __table_args__ = (
        UniqueConstraint("platform", "platform_creator_id", name="uq_creators_platform_identity"),
        CheckConstraint("followers >= 0", name="followers_nonnegative"),
        CheckConstraint("total_views >= 0", name="total_views_nonnegative"),
    )
    platform: Mapped[str] = mapped_column(String(32))
    platform_creator_id: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(200))
    profile_url: Mapped[str | None] = mapped_column(String(2048))
    avatar_url: Mapped[str | None] = mapped_column(String(2048))
    followers: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    total_views: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
