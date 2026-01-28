from celery import Celery

REDIS_URL = "redis://localhost:6379/0"

celery_app = Celery(
    "qshield",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# ✅ tasks 모듈을 강제로 로드 (가장 확실)
celery_app.conf.include = ["app.tasks"]

# ✅ 추가로 autodiscover도 켜두기 (나중에 앱 커져도 안전)
celery_app.autodiscover_tasks(["app"])
