from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate
from app.services.common import commit, get_or_404


def list_records(db: Session, offset: int, limit: int, guide_id: UUID | None):
    query = select(Comment)
    if guide_id is not None:
        query = query.where(Comment.guide_id == guide_id)
    return db.scalars(
        query.order_by(Comment.created_at, Comment.id).offset(offset).limit(limit)
    ).all()


def create(db: Session, payload: CommentCreate):
    record = Comment(**payload.model_dump())
    db.add(record)
    commit(db)
    db.refresh(record)
    return record


def get(db: Session, record_id: UUID):
    return get_or_404(db, Comment, record_id)


def update(db: Session, record_id: UUID, payload: CommentUpdate):
    record = get(db, record_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    commit(db)
    db.refresh(record)
    return record


def delete(db: Session, record_id: UUID):
    db.delete(get(db, record_id))
    commit(db)
