from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.guide import Guide
from app.schemas.guide import GuideCreate, GuideUpdate
from app.services.common import commit, get_or_404


def list_records(
    db: Session, offset: int, limit: int, creator_id: UUID | None, platform: str | None
):
    query = select(Guide)
    if creator_id is not None:
        query = query.where(Guide.creator_id == creator_id)
    if platform is not None:
        query = query.where(Guide.platform == platform)
    return db.scalars(query.order_by(Guide.created_at, Guide.id).offset(offset).limit(limit)).all()


def create(db: Session, payload: GuideCreate):
    record = Guide(**payload.model_dump())
    db.add(record)
    commit(db)
    db.refresh(record)
    return record


def get(db: Session, record_id: UUID):
    return get_or_404(db, Guide, record_id)


def update(db: Session, record_id: UUID, payload: GuideUpdate):
    record = get(db, record_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    commit(db)
    db.refresh(record)
    return record


def delete(db: Session, record_id: UUID):
    db.delete(get(db, record_id))
    commit(db)
