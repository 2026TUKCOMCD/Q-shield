from __future__ import annotations

import asyncio
import uuid as uuid_lib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai_module.orchestrator import compute_and_persist_ai_analysis
from app.celery_app import celery_app
from app.config import DATABASE_URL_SYNC

engine = create_engine(DATABASE_URL_SYNC, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@celery_app.task(name="run_ai_analysis")
def run_ai_analysis(scan_uuid: str):
    db = SessionLocal()
    try:
        scan_uuid_obj = uuid_lib.UUID(scan_uuid)
        result = asyncio.run(compute_and_persist_ai_analysis(scan_uuid_obj, db))
        return result.model_dump() if result is not None else None
    finally:
        db.close()
