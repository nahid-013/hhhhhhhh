"""
Celery задачи для системы энергии
"""
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from workers.celery_app import celery_app
from backend.core.config import settings
from backend.db.models.spirit import PlayerSpirit, SpiritTemplate


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


async def _tick_energy_async():
    """
    Асинхронная функция для восстановления энергии

    Логика:
    - Для каждого player_spirit добавить +5 energy (до max_energy)
    - max_energy = base_max_energy + (generation * 5)
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Получаем всех спиритов с их шаблонами
            result = await session.execute(
                select(PlayerSpirit, SpiritTemplate)
                .join(SpiritTemplate, PlayerSpirit.spirit_template_id == SpiritTemplate.id)
                .where(PlayerSpirit.energy < PlayerSpirit.base_max_energy + (PlayerSpirit.generation * 5))
            )
            spirits_to_update = result.all()

            updated_count = 0
            for player_spirit, template in spirits_to_update:
                # Вычисляем max_energy
                max_energy = player_spirit.base_max_energy + (player_spirit.generation * 5)

                # Добавляем +5, но не больше max_energy
                new_energy = min(player_spirit.energy + 5, max_energy)

                # Обновляем энергию
                await session.execute(
                    update(PlayerSpirit)
                    .where(PlayerSpirit.id == player_spirit.id)
                    .values(energy=new_energy)
                )
                updated_count += 1

            await session.commit()

            return {
                "status": "ok",
                "spirits_updated": updated_count,
                "message": f"Energy restored for {updated_count} spirits"
            }


@celery_app.task(name="workers.tasks.energy.tick_energy")
def tick_energy():
    """
    Восстанавливает +5 энергии каждому спириту каждые 10 минут

    Формула:
    - energy = min(current_energy + 5, max_energy)
    - max_energy = base_max_energy + (generation * 5)
    """
    try:
        # Запускаем async функцию в sync контексте Celery
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(_tick_energy_async())
        return result
    except Exception as e:
        print(f"Error in tick_energy: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


async def _restore_spirit_energy_async(spirit_id: int, amount: int = None):
    """
    Асинхронная функция для мгновенного восстановления энергии

    Args:
        spirit_id: ID спирита
        amount: Количество энергии для восстановления (если None - до максимума)
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Получаем спирита
            result = await session.execute(
                select(PlayerSpirit)
                .where(PlayerSpirit.id == spirit_id)
            )
            spirit = result.scalar_one_or_none()

            if not spirit:
                return {
                    "status": "error",
                    "message": "Spirit not found"
                }

            # Вычисляем max_energy
            max_energy = spirit.base_max_energy + (spirit.generation * 5)

            # Восстанавливаем энергию
            if amount is None:
                new_energy = max_energy
            else:
                new_energy = min(spirit.energy + amount, max_energy)

            # Обновляем
            await session.execute(
                update(PlayerSpirit)
                .where(PlayerSpirit.id == spirit_id)
                .values(energy=new_energy)
            )

            await session.commit()

            return {
                "status": "ok",
                "previous_energy": spirit.energy,
                "new_energy": new_energy,
                "max_energy": max_energy
            }


@celery_app.task(name="workers.tasks.energy.restore_spirit_energy")
def restore_spirit_energy(spirit_id: int, amount: int = None):
    """
    Мгновенное восстановление энергии спирита (для paid instant restore)

    Args:
        spirit_id: ID спирита
        amount: Количество энергии (если None - до максимума)
    """
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(_restore_spirit_energy_async(spirit_id, amount))
        return result
    except Exception as e:
        print(f"Error in restore_spirit_energy: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
