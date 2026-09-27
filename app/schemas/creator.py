from typing import ClassVar

from pydantic import AwareDatetime, Field

from app.schemas.base import InputModel, PatchModel, RecordRead


class CreatorCreate(InputModel):
    platform: str = Field(..., min_length=1, max_length=32)
    platform_creator_id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=200)
    profile_url: str | None = Field(None, max_length=2048)
    avatar_url: str | None = Field(None, max_length=2048)
    followers: int = Field(0, ge=0, le=9223372036854775807)
    total_views: int = Field(0, ge=0, le=9223372036854775807)
    last_crawled_at: AwareDatetime | None = Field(None)


class CreatorUpdate(PatchModel):
    nullable_fields: ClassVar[set[str]] = {"profile_url", "avatar_url", "last_crawled_at"}
    platform: str | None = Field(None, min_length=1, max_length=32)
    platform_creator_id: str | None = Field(None, min_length=1, max_length=128)
    name: str | None = Field(None, min_length=1, max_length=200)
    profile_url: str | None = Field(None, max_length=2048)
    avatar_url: str | None = Field(None, max_length=2048)
    followers: int | None = Field(None, ge=0, le=9223372036854775807)
    total_views: int | None = Field(None, ge=0, le=9223372036854775807)
    last_crawled_at: AwareDatetime | None = Field(None)


class CreatorRead(RecordRead):
    platform: str
    platform_creator_id: str
    name: str
    profile_url: str | None
    avatar_url: str | None
    followers: int
    total_views: int
    last_crawled_at: AwareDatetime | None
