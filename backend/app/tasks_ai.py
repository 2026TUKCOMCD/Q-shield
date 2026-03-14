from __future__ import annotations

import asyncio
import logging
import uuid as uuid_lib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai_module.orchestrator import compute_and_persist_ai_analysis
from app.celery_app import celery_app
from app.config import DATABASE_URL_SYNC

engine = create_engine(DATABASE_URL_SYNC, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
logger = logging.getLogger(__name__)


@celery_app.task(name="run_ai_analysis")
def run_ai_analysis(scan_uuid: str):
    db = SessionLocal()
    try:
        logger.info("ai_analysis_task stage=start scan_uuid=%s", scan_uuid)
        scan_uuid_obj = uuid_lib.UUID(scan_uuid)
        result = asyncio.run(compute_and_persist_ai_analysis(scan_uuid_obj, db))
        logger.info(
            "ai_analysis_task stage=done scan_uuid=%s mode=%s",
            scan_uuid,
            getattr(result, "analysis_mode", None),
        )
        return result.model_dump() if result is not None else None
    except Exception as exc:
        logger.exception("ai_analysis_task stage=failed scan_uuid=%s reason=%s", scan_uuid, str(exc))
        raise
    finally:
        db.close()
