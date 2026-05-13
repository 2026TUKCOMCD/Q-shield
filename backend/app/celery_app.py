import os
import sys

from celery import Celery

from app.config import REDIS_URL

BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# macOS prefork + ObjC fork() crash → solo pool. Windows/Linux use default (prefork).
_worker_pool = os.getenv("CELERY_POOL", "solo" if sys.platform == "darwin" else "prefork")

celery_app = Celery(
    "qshield",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.tasks", "app.tasks_ai"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    enable_utc=True,
    worker_pool=_worker_pool,
)
