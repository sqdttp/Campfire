from typing import ClassVar
from uuid import UUID

from pydantic import AwareDatetime, Field

from app.schemas.base import InputModel, PatchModel, RecordRead


class GuideCreate(InputModel):
    creator_id: UUID = Field(...)
    platform: str = Field(..., min_length=1, max_length=32)
    platform_content_id: str = Field(..., min_length=1, max_length=128)
    url: str = Field(..., min_length=1, max_length=2048)
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None)
    transcript: str | None = Field(None)
    published_at: AwareDatetime | None = Field(None)
    view_count: int = Field(0, ge=0, le=9223372036854775807)
    like_count: int = Field(0, ge=0, le=9223372036854775807)
    favorite_count: int = Field(0, ge=0, le=9223372036854775807)
    coin_count: int = Field(0, ge=0, le=9223372036854775807)
    comment_count: int = Field(0, ge=0, le=9223372036854775807)
    content_hash: str | None = Field(None, max_length=64)
    crawl_status: str = Field("pending", min_length=1, max_length=32)
    analysis_status: str = Field("pending", min_length=1, max_length=32)
    last_crawled_at: AwareDatetime | None = Field(None)


class GuideUpdate(PatchModel):
    nullable_fields: ClassVar[set[str]] = {
        "description",
        "transcript",
        "published_at",
        "content_hash",
        "last_crawled_at",
    }
    creator_id: UUID | None = Field(None)
    platform: str | None = Field(None, min_length=1, max_length=32)
    platform_content_id: str | None = Field(None, min_length=1, max_length=128)
    url: str | None = Field(None, min_length=1, max_length=2048)
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None)
    transcript: str | None = Field(None)
    published_at: AwareDatetime | None = Field(None)
    view_count: int | None = Field(None, ge=0, le=9223372036854775807)
    like_count: int | None = Field(None, ge=0, le=9223372036854775807)
    favorite_count: int | None = Field(None, ge=0, le=9223372036854775807)
    coin_count: int | None = Field(None, ge=0, le=9223372036854775807)
    comment_count: int | None = Field(None, ge=0, le=9223372036854775807)
    content_hash: str | None = Field(None, max_length=64)
    crawl_status: str | None = Field(None, min_length=1, max_length=32)
    analysis_status: str | None = Field(None, min_length=1, max_length=32)
    last_crawled_at: AwareDatetime | None = Field(None)


class GuideRead(RecordRead):
    creator_id: UUID
    platform: str
    platform_content_id: str
    url: str
    title: str
    description: str | None
    transcript: str | None
    published_at: AwareDatetime | None
    view_count: int
    like_count: int
    favorite_count: int
    coin_count: int
    comment_count: int
    content_hash: str | None
    crawl_status: str
    analysis_status: str
    last_crawled_at: AwareDatetime | None
