"""
Celery приложение для фоновых задач
"""
from celery import Celery
from celery.schedules import crontab

from backend.core.config import settings

# Создание Celery приложения
celery_app = Celery(
    "hunt_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "workers.tasks.energy",
        "workers.tasks.capsules",
        "workers.tasks.economy",
    ],
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Расписание для периодических задач (Celery Beat)
celery_app.conf.beat_schedule = {
    # Восстановление энергии каждые 10 минут
    "tick-energy-every-10-minutes": {
        "task": "workers.tasks.energy.tick_energy",
        "schedule": crontab(minute="*/10"),  # Каждые 10 минут
    },
    # Обработка выводов TON каждый час
    "process-withdrawals-every-hour": {
        "task": "workers.tasks.economy.process_withdrawals",
        "schedule": crontab(minute=0),  # Каждый час в :00
    },
    # Обновление лидербордов каждые 15 минут
    # "update-leaderboards": {
    #     "task": "workers.tasks.leaderboards.update_leaderboards",
    #     "schedule": crontab(minute="*/15"),
    # },
}


if __name__ == "__main__":
    celery_app.start()
