from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.guide import GuideCreate, GuideRead, GuideUpdate
from app.services import guide_service as service

router = APIRouter(prefix="/guides", tags=["guides"])
DB = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[GuideRead])
def list_records(
    db: DB,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    creator_id: UUID | None = None,
    platform: str | None = None,
):
    return service.list_records(db, offset, limit, creator_id, platform)


@router.post("", response_model=GuideRead, status_code=201)
def create(payload: GuideCreate, db: DB):
    return service.create(db, payload)


@router.get("/{record_id}", response_model=GuideRead)
def get(record_id: UUID, db: DB):
    return service.get(db, record_id)


@router.patch("/{record_id}", response_model=GuideRead)
def update(record_id: UUID, payload: GuideUpdate, db: DB):
    return service.update(db, record_id, payload)


@router.delete("/{record_id}", status_code=204)
def delete(record_id: UUID, db: DB):
    service.delete(db, record_id)
    return Response(status_code=204)
