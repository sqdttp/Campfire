from uuid import UUID

from pydantic import Field, field_validator

from app.crawlers.bilibili import extract_bvid
from app.schemas.base import InputModel


class BilibiliVideoImport(InputModel):
    video: str = Field(..., min_length=1, max_length=2048)
    fetch_comments: bool = True
    max_comments: int = Field(100, ge=0, le=500)

    @field_validator("video")
    @classmethod
    def validate_video(cls, value: str) -> str:
        extract_bvid(value)
        return value


class BilibiliImportResult(InputModel):
    bvid: str
    creator_id: UUID
    guide_id: UUID
    creator_created: bool
    guide_created: bool
    comments_fetched: int
    comments_created: int
    comments_updated: int
