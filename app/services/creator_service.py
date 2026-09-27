from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.creator import Creator
from app.schemas.creator import CreatorCreate, CreatorUpdate
from app.services.common import commit, get_or_404


def list_records(db: Session, offset: int, limit: int, platform: str | None):
    query = select(Creator)
    if platform is not None:
        query = query.where(Creator.platform == platform)
    return db.scalars(
        query.order_by(Creator.created_at, Creator.id).offset(offset).limit(limit)
    ).all()


def create(db: Session, payload: CreatorCreate):
    record = Creator(**payload.model_dump())
    db.add(record)
    commit(db)
    db.refresh(record)
    return record


def get(db: Session, record_id: UUID):
    return get_or_404(db, Creator, record_id)


def update(db: Session, record_id: UUID, payload: CreatorUpdate):
    record = get(db, record_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    commit(db)
    db.refresh(record)
    return record


def delete(db: Session, record_id: UUID):
    db.delete(get(db, record_id))
    commit(db)
