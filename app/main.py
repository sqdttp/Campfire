from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import comments, creators, guides, imports
from app.core.config import get_settings
from app.core.database import get_db

app = FastAPI(title=get_settings().app_name, version="0.1.0")
app.include_router(creators.router)
app.include_router(guides.router)
app.include_router(comments.router)
app.include_router(imports.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def readiness(db: Annotated[Session, Depends(get_db)]):
    try:
        # Verify migration-created tables as well as the connection.
        for table in ("creators", "guides", "comments"):
            db.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database is not ready") from None
    return {"status": "ready"}
