from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crawlers.bilibili import BilibiliAPIError, BilibiliClient, get_bilibili_client
from app.schemas.bilibili import BilibiliImportResult, BilibiliVideoImport
from app.services import bilibili_import_service

router = APIRouter(prefix="/imports", tags=["imports"])
DB = Annotated[Session, Depends(get_db)]
Bilibili = Annotated[BilibiliClient, Depends(get_bilibili_client)]


@router.post("/bilibili/videos", response_model=BilibiliImportResult)
def import_bilibili_video(payload: BilibiliVideoImport, db: DB, client: Bilibili):
    try:
        return bilibili_import_service.import_video(db, payload, client)
    except BilibiliAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502, detail="Bilibili returned incomplete video data"
        ) from exc
