"""
Celery задачи для системы капсул
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from workers.celery_app import celery_app
from backend.core.config import settings


# Создаем async engine для Celery задач
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def _finish_capsule_opening_async(player_capsule_id: int, owner_id: int):
    """
    Асинхронная функция для завершения открытия капсулы

    Args:
        player_capsule_id: ID капсулы игрока
        owner_id: ID владельца

    Returns:
        dict с результатом открытия
    """
    from backend.services.capsule_service import open_capsule_synchronous

    async with AsyncSessionLocal() as session:
        # Используем существующую логику из capsule_service
        result = await open_capsule_synchronous(session, player_capsule_id, owner_id)
        return result


@celery_app.task(name="workers.tasks.capsules.finish_capsule_opening")
def finish_capsule_opening(player_capsule_id: int, owner_id: int):
    """
    Завершает открытие капсулы после истечения таймера

    Логика:
    1. Получить капсулу из БД
    2. Weighted random выбор спирита из drops
    3. Создать player_spirit
    4. Обновить player_capsules (decrement quantity)
    5. Отправить уведомление пользователю (TODO: Sprint 6)

    Args:
        player_capsule_id: ID капсулы игрока
        owner_id: ID владельца
    """
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(_finish_capsule_opening_async(player_capsule_id, owner_id))

        if result["success"]:
            # TODO: Отправить уведомление пользователю через WebSocket
            # Будет реализовано в Sprint 6
            return {
                "status": "ok",
                "player_capsule_id": player_capsule_id,
                "spirit_id": result["spirit"].id if result["spirit"] else None,
                "message": "Capsule opened successfully"
            }
        else:
            return {
                "status": "error",
                "player_capsule_id": player_capsule_id,
                "message": result["error"]
            }

    except Exception as e:
        print(f"Error in finish_capsule_opening: {str(e)}")
        return {
            "status": "error",
            "player_capsule_id": player_capsule_id,
            "message": str(e)
        }
