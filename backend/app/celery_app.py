import os
from celery import Celery
from app.config import REDIS_URL

BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

celery_app = Celery(
    "qshield",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.tasks"],  # ✅ tasks 자동 로드
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    enable_utc=True,
)
