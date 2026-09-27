from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.creator import CreatorCreate, CreatorRead, CreatorUpdate
from app.services import creator_service as service

router = APIRouter(prefix="/creators", tags=["creators"])
DB = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[CreatorRead])
def list_records(
    db: DB,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    platform: str | None = None,
):
    return service.list_records(db, offset, limit, platform)


@router.post("", response_model=CreatorRead, status_code=201)
def create(payload: CreatorCreate, db: DB):
    return service.create(db, payload)


@router.get("/{record_id}", response_model=CreatorRead)
def get(record_id: UUID, db: DB):
    return service.get(db, record_id)


@router.patch("/{record_id}", response_model=CreatorRead)
def update(record_id: UUID, payload: CreatorUpdate, db: DB):
    return service.update(db, record_id, payload)


@router.delete("/{record_id}", status_code=204)
def delete(record_id: UUID, db: DB):
    service.delete(db, record_id)
    return Response(status_code=204)
