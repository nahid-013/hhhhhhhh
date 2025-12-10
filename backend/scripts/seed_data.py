"""
Скрипт для заполнения начальных данных БД
"""
import asyncio
import sys
from pathlib import Path

# Добавляем родительскую директорию в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import AsyncSessionLocal
from backend.db.models.element import Element
from backend.db.models.rarity import Rarity


async def seed_elements(session: AsyncSession):
    """Заполнение таблицы стихий"""
    elements_data = [
        {
            "code": "fire",
            "name_ru": "Огонь",
            "name_en": "Fire",
            "icon_url": "/assets/elements/fire.png",
        },
        {
            "code": "water",
            "name_ru": "Вода",
            "name_en": "Water",
            "icon_url": "/assets/elements/water.png",
        },
        {
            "code": "earth",
            "name_ru": "Земля",
            "name_en": "Earth",
            "icon_url": "/assets/elements/earth.png",
        },
        {
            "code": "air",
            "name_ru": "Воздух",
            "name_en": "Air",
            "icon_url": "/assets/elements/air.png",
        },
        {
            "code": "light",
            "name_ru": "Свет",
            "name_en": "Light",
            "icon_url": "/assets/elements/light.png",
        },
        {
            "code": "dark",
            "name_ru": "Тьма",
            "name_en": "Dark",
            "icon_url": "/assets/elements/dark.png",
        },
    ]

    for data in elements_data:
        element = Element(**data)
        session.add(element)

    await session.commit()
    print(f"✓ Создано {len(elements_data)} стихий")


async def seed_rarities(session: AsyncSession):
    """Заполнение таблицы редкостей"""
    rarities_data = [
        {
            "code": "common",
            "name_ru": "Обычный",
            "name_en": "Common",
            "power_factor": 1.0,
            "icon_url": "/assets/rarities/common.png",
        },
        {
            "code": "rare",
            "name_ru": "Редкий",
            "name_en": "Rare",
            "power_factor": 1.2,
            "icon_url": "/assets/rarities/rare.png",
        },
        {
            "code": "epic",
            "name_ru": "Эпический",
            "name_en": "Epic",
            "power_factor": 1.5,
            "icon_url": "/assets/rarities/epic.png",
        },
        {
            "code": "legendary",
            "name_ru": "Легендарный",
            "name_en": "Legendary",
            "power_factor": 2.0,
            "icon_url": "/assets/rarities/legendary.png",
        },
        {
            "code": "mythical",
            "name_ru": "Мифический",
            "name_en": "Mythical",
            "power_factor": 3.0,
            "icon_url": "/assets/rarities/mythical.png",
        },
    ]

    for data in rarities_data:
        rarity = Rarity(**data)
        session.add(rarity)

    await session.commit()
    print(f"✓ Создано {len(rarities_data)} редкостей")


async def main():
    """Основная функция для запуска seed"""
    print("Начинаю заполнение базы данных начальными данными...")

    async with AsyncSessionLocal() as session:
        try:
            await seed_elements(session)
            await seed_rarities(session)
            print("\n✓ Все данные успешно загружены!")
        except Exception as e:
            print(f"\n✗ Ошибка при заполнении данных: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
