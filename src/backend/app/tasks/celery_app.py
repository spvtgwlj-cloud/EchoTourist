"""Celery 异步任务配置。"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "echo_tours",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.search_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "app.tasks.maintenance_tasks.cleanup_expired_sessions",
            "schedule": 86400,  # daily
        },
        "reindex-all-tours": {
            "task": "app.tasks.search_tasks.reindex_all_tours",
            "schedule": 86400,  # daily — rebuild ES search index
        },
    },
)
