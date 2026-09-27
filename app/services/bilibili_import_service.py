import hashlib
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crawlers.bilibili import BilibiliClient, extract_bvid
from app.models.comment import Comment
from app.models.creator import Creator
from app.models.guide import Guide
from app.schemas.bilibili import BilibiliImportResult, BilibiliVideoImport
from app.services.common import commit


def import_video(
    db: Session, request: BilibiliVideoImport, client: BilibiliClient
) -> BilibiliImportResult:
    bvid = extract_bvid(request.video)
    video = client.get_video(bvid)
    owner = video.get("owner") or {}
    stat = video.get("stat") or {}
    aid = int(video["aid"])
    fetched_comments = (
        client.get_comments(aid, request.max_comments) if request.fetch_comments else []
    )
    crawled_at = datetime.now(UTC)

    creator, creator_created = _upsert_creator(db, owner, crawled_at)
    db.flush()
    guide, guide_created = _upsert_guide(db, creator, video, stat, bvid, crawled_at)
    db.flush()
    comments_created, comments_updated = _upsert_comments(db, guide, fetched_comments, crawled_at)
    commit(db)
    db.refresh(creator)
    db.refresh(guide)

    return BilibiliImportResult(
        bvid=bvid,
        creator_id=creator.id,
        guide_id=guide.id,
        creator_created=creator_created,
        guide_created=guide_created,
        comments_fetched=len(fetched_comments),
        comments_created=comments_created,
        comments_updated=comments_updated,
    )


def _upsert_creator(
    db: Session, owner: dict[str, Any], crawled_at: datetime
) -> tuple[Creator, bool]:
    platform_creator_id = str(owner["mid"])
    creator = db.scalar(
        select(Creator).where(
            Creator.platform == "bilibili",
            Creator.platform_creator_id == platform_creator_id,
        )
    )
    created = creator is None
    if creator is None:
        creator = Creator(
            platform="bilibili",
            platform_creator_id=platform_creator_id,
            name=str(owner.get("name") or platform_creator_id),
        )
        db.add(creator)
    creator.name = str(owner.get("name") or creator.name)
    creator.profile_url = f"https://space.bilibili.com/{platform_creator_id}"
    creator.avatar_url = _optional_string(owner.get("face"))
    creator.last_crawled_at = crawled_at
    return creator, created


def _upsert_guide(
    db: Session,
    creator: Creator,
    video: dict[str, Any],
    stat: dict[str, Any],
    bvid: str,
    crawled_at: datetime,
) -> tuple[Guide, bool]:
    guide = db.scalar(
        select(Guide).where(Guide.platform == "bilibili", Guide.platform_content_id == bvid)
    )
    created = guide is None
    title = str(video.get("title") or bvid)
    description = _optional_string(video.get("desc"))
    content_hash = hashlib.sha256(f"{title}\0{description or ''}".encode()).hexdigest()
    if guide is None:
        guide = Guide(
            creator_id=creator.id,
            platform="bilibili",
            platform_content_id=bvid,
            url=f"https://www.bilibili.com/video/{bvid}",
            title=title,
        )
        db.add(guide)
    elif guide.content_hash != content_hash:
        guide.analysis_status = "pending"

    guide.creator_id = creator.id
    guide.url = f"https://www.bilibili.com/video/{bvid}"
    guide.title = title
    guide.description = description
    guide.published_at = _timestamp(video.get("pubdate"))
    guide.view_count = _nonnegative_int(stat.get("view"))
    guide.like_count = _nonnegative_int(stat.get("like"))
    guide.favorite_count = _nonnegative_int(stat.get("favorite"))
    guide.coin_count = _nonnegative_int(stat.get("coin"))
    guide.comment_count = _nonnegative_int(stat.get("reply"))
    guide.content_hash = content_hash
    guide.crawl_status = "crawled"
    guide.last_crawled_at = crawled_at
    return guide, created


def _upsert_comments(
    db: Session,
    guide: Guide,
    replies: list[dict[str, Any]],
    crawled_at: datetime,
) -> tuple[int, int]:
    ids = [str(reply.get("rpid")) for reply in replies if reply.get("rpid")]
    existing = {
        comment.platform_comment_id: comment
        for comment in db.scalars(
            select(Comment).where(
                Comment.guide_id == guide.id, Comment.platform_comment_id.in_(ids)
            )
        )
    }
    created = 0
    updated = 0
    for reply in replies:
        reply_id = str(reply.get("rpid") or "")
        if not reply_id:
            continue
        comment = existing.get(reply_id)
        if comment is None:
            comment = Comment(guide_id=guide.id, platform_comment_id=reply_id, content="")
            db.add(comment)
            existing[reply_id] = comment
            created += 1
        else:
            updated += 1
        member = reply.get("member") or {}
        content = reply.get("content") or {}
        parent = reply.get("parent") or reply.get("root")
        comment.parent_comment_id = str(parent) if parent else None
        comment.user_platform_id = _optional_string(member.get("mid"))
        comment.content = str(content.get("message") or "")
        comment.likes = _nonnegative_int(reply.get("like"))
        comment.reply_count = _nonnegative_int(reply.get("rcount"))
        comment.published_at = _timestamp(reply.get("ctime"))
        comment.crawled_at = crawled_at
    return created, updated


def _timestamp(value: Any) -> datetime | None:
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(timestamp, UTC) if timestamp > 0 else None


def _nonnegative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None
