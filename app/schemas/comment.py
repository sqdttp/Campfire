from typing import ClassVar
from uuid import UUID

from pydantic import AwareDatetime, Field

from app.schemas.base import InputModel, PatchModel, RecordRead


class CommentCreate(InputModel):
    guide_id: UUID = Field(...)
    platform_comment_id: str = Field(..., min_length=1, max_length=128)
    parent_comment_id: str | None = Field(None, max_length=128)
    user_platform_id: str | None = Field(None, max_length=128)
    content: str = Field(..., min_length=1)
    likes: int = Field(0, ge=0, le=9223372036854775807)
    reply_count: int = Field(0, ge=0, le=9223372036854775807)
    published_at: AwareDatetime | None = Field(None)
    crawled_at: AwareDatetime | None = Field(None)


class CommentUpdate(PatchModel):
    nullable_fields: ClassVar[set[str]] = {
        "parent_comment_id",
        "user_platform_id",
        "published_at",
        "crawled_at",
    }
    guide_id: UUID | None = Field(None)
    platform_comment_id: str | None = Field(None, min_length=1, max_length=128)
    parent_comment_id: str | None = Field(None, max_length=128)
    user_platform_id: str | None = Field(None, max_length=128)
    content: str | None = Field(None, min_length=1)
    likes: int | None = Field(None, ge=0, le=9223372036854775807)
    reply_count: int | None = Field(None, ge=0, le=9223372036854775807)
    published_at: AwareDatetime | None = Field(None)
    crawled_at: AwareDatetime | None = Field(None)


class CommentRead(RecordRead):
    guide_id: UUID
    platform_comment_id: str
    parent_comment_id: str | None
    user_platform_id: str | None
    content: str
    likes: int
    reply_count: int
    published_at: AwareDatetime | None
    crawled_at: AwareDatetime | None
