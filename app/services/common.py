from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Base


def get_or_404[T: Base](db: Session, model: type[T], record_id: UUID) -> T:
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


def commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Data conflict: duplicate platform identifier or invalid/dependent reference",
        ) from None
