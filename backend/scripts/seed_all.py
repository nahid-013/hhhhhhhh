"""
Seed скрипт для заполнения базы данных начальными данными
Запускать: PYTHONPATH=/Users/nahidgabibov/Desktop/last_hunt python3 backend/scripts/seed_all.py
"""
import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings
from backend.db.models.element import Element
from backend.db.models.rarity import Rarity
from backend.db.models.capsule import CapsuleTemplate, CapsuleDrop
from backend.db.models.boost import BoostTemplate
from backend.db.models.spirit import SpiritTemplate
from backend.db.models.slot import SlotTemplate


async def clear_all_data(session: AsyncSession):
    """Очистка всех данных (опционально, для чистого старта)"""
    print("⚠️  Очистка существующих данных...")
    # Порядок важен из-за FK constraints
    await session.execute("DELETE FROM capsule_drops")
    await session.execute("DELETE FROM player_spirits")
    await session.execute("DELETE FROM player_slots")
    await session.execute("DELETE FROM player_boosts")
    await session.execute("DELETE FROM player_capsules")
    await session.execute("DELETE FROM spirits_template")
    await session.execute("DELETE FROM boost_template")
    await session.execute("DELETE FROM capsule_template")
    await session.execute("DELETE FROM slots_template")
    await session.execute("DELETE FROM rarities")
    await session.execute("DELETE FROM elements")
    await session.commit()
    print("✅ Данные очищены")


async def seed_elements(session: AsyncSession):
    """Создание элементов (стихий)"""
    print("\n🔥 Создание элементов...")
    elements_data = [
        {"code": "fire", "name_ru": "Огонь", "name_en": "Fire", "icon_url": "/icons/fire.png"},
        {"code": "water", "name_ru": "Вода", "name_en": "Water", "icon_url": "/icons/water.png"},
        {"code": "earth", "name_ru": "Земля", "name_en": "Earth", "icon_url": "/icons/earth.png"},
        {"code": "air", "name_ru": "Воздух", "name_en": "Air", "icon_url": "/icons/air.png"},
        {"code": "light", "name_ru": "Свет", "name_en": "Light", "icon_url": "/icons/light.png"},
        {"code": "dark", "name_ru": "Тьма", "name_en": "Dark", "icon_url": "/icons/dark.png"},
    ]

    elements = []
    for data in elements_data:
        element = Element(**data)
        session.add(element)
        elements.append(element)

    await session.commit()
    print(f"✅ Создано {len(elements)} элементов")
    return {e.code: e for e in elements}


async def seed_rarities(session: AsyncSession):
    """Создание редкостей"""
    print("\n💎 Создание редкостей...")
    rarities_data = [
        {"code": "common", "name_ru": "Обычный", "name_en": "Common", "icon_url": "/icons/common.png", "power_factor": Decimal("1.0")},
        {"code": "rare", "name_ru": "Редкий", "name_en": "Rare", "icon_url": "/icons/rare.png", "power_factor": Decimal("1.2")},
        {"code": "epic", "name_ru": "Эпический", "name_en": "Epic", "icon_url": "/icons/epic.png", "power_factor": Decimal("1.5")},
        {"code": "legendary", "name_ru": "Легендарный", "name_en": "Legendary", "icon_url": "/icons/legendary.png", "power_factor": Decimal("2.0")},
        {"code": "mythical", "name_ru": "Мифический", "name_en": "Mythical", "icon_url": "/icons/mythical.png", "power_factor": Decimal("3.0")},
    ]

    rarities = []
    for data in rarities_data:
        rarity = Rarity(**data)
        session.add(rarity)
        rarities.append(rarity)

    await session.commit()
    print(f"✅ Создано {len(rarities)} редкостей")
    return {r.code: r for r in rarities}


async def seed_capsules(session: AsyncSession, elements: dict, rarities: dict):
    """Создание шаблонов капсул"""
    print("\n📦 Создание капсул...")
    capsules = []

    # Создаем по 2 капсулы для каждого элемента (common и rare)
    for element_code, element in elements.items():
        # Common капсула (дешевая, быстрое открытие)
        common_capsule = CapsuleTemplate(
            code=f"{element_code}_common",
            element_id=element.id,
            rarity_id=rarities["common"].id,
            name_ru=f"Обычная капсула {element.name_ru}",
            name_en=f"Common {element.name_en} Capsule",
            open_time_seconds=0,  # Мгновенное открытие
            price_in_ton=Decimal("0"),
            price_lumens=Decimal("100"),
            icon_url=f"/icons/capsule_{element_code}_common.png",
            is_available=True,
            amount=0,  # Безлимит
            fast_open_cost=Decimal("0"),
        )
        session.add(common_capsule)
        capsules.append(common_capsule)

        # Rare капсула (дороже, может требовать времени)
        rare_capsule = CapsuleTemplate(
            code=f"{element_code}_rare",
            element_id=element.id,
            rarity_id=rarities["rare"].id,
            name_ru=f"Редкая капсула {element.name_ru}",
            name_en=f"Rare {element.name_en} Capsule",
            open_time_seconds=0,  # Пока мгновенное (в Sprint 4 добавим таймеры)
            price_in_ton=Decimal("0.5"),
            price_lumens=Decimal("500"),
            icon_url=f"/icons/capsule_{element_code}_rare.png",
            is_available=True,
            amount=0,
            fast_open_cost=Decimal("50"),
        )
        session.add(rare_capsule)
        capsules.append(rare_capsule)

    await session.commit()
    print(f"✅ Создано {len(capsules)} капсул")
    return capsules


async def seed_spirits(session: AsyncSession, elements: dict, rarities: dict, capsules: list):
    """Создание шаблонов спиритов"""
    print("\n👻 Создание спиритов...")
    spirits = []

    # Создаем по 3 спирита для каждого элемента (разных редкостей)
    spirit_templates = {
        "fire": [
            {"suffix": "flame", "name_ru": "Пламя", "name_en": "Flame", "rarity": "common", "gen": 1},
            {"suffix": "inferno", "name_ru": "Инферно", "name_en": "Inferno", "rarity": "rare", "gen": 1},
            {"suffix": "phoenix", "name_ru": "Феникс", "name_en": "Phoenix", "rarity": "epic", "gen": 2},
        ],
        "water": [
            {"suffix": "stream", "name_ru": "Ручей", "name_en": "Stream", "rarity": "common", "gen": 1},
            {"suffix": "wave", "name_ru": "Волна", "name_en": "Wave", "rarity": "rare", "gen": 1},
            {"suffix": "tsunami", "name_ru": "Цунами", "name_en": "Tsunami", "rarity": "epic", "gen": 2},
        ],
        "earth": [
            {"suffix": "stone", "name_ru": "Камень", "name_en": "Stone", "rarity": "common", "gen": 1},
            {"suffix": "boulder", "name_ru": "Валун", "name_en": "Boulder", "rarity": "rare", "gen": 1},
            {"suffix": "mountain", "name_ru": "Гора", "name_en": "Mountain", "rarity": "epic", "gen": 2},
        ],
        "air": [
            {"suffix": "breeze", "name_ru": "Бриз", "name_en": "Breeze", "rarity": "common", "gen": 1},
            {"suffix": "gale", "name_ru": "Шторм", "name_en": "Gale", "rarity": "rare", "gen": 1},
            {"suffix": "hurricane", "name_ru": "Ураган", "name_en": "Hurricane", "rarity": "epic", "gen": 2},
        ],
        "light": [
            {"suffix": "spark", "name_ru": "Искра", "name_en": "Spark", "rarity": "common", "gen": 1},
            {"suffix": "beam", "name_ru": "Луч", "name_en": "Beam", "rarity": "rare", "gen": 1},
            {"suffix": "radiance", "name_ru": "Сияние", "name_en": "Radiance", "rarity": "epic", "gen": 2},
        ],
        "dark": [
            {"suffix": "shadow", "name_ru": "Тень", "name_en": "Shadow", "rarity": "common", "gen": 1},
            {"suffix": "void", "name_ru": "Бездна", "name_en": "Void", "rarity": "rare", "gen": 1},
            {"suffix": "abyss", "name_ru": "Пучина", "name_en": "Abyss", "rarity": "epic", "gen": 2},
        ],
    }

    # Базовые статы по редкостям
    stats_by_rarity = {
        "common": {"run": 1, "jump": 1, "swim": 1, "dives": 1, "fly": 1, "maneuver": 1, "energy": 100},
        "rare": {"run": 3, "jump": 3, "swim": 3, "dives": 3, "fly": 3, "maneuver": 3, "energy": 120},
        "epic": {"run": 5, "jump": 5, "swim": 5, "dives": 5, "fly": 5, "maneuver": 5, "energy": 150},
    }

    for element_code, templates in spirit_templates.items():
        element = elements[element_code]
        for template in templates:
            rarity = rarities[template["rarity"]]
            stats = stats_by_rarity[template["rarity"]]

            spirit = SpiritTemplate(
                code=f"{element_code}_{template['suffix']}",
                element_id=element.id,
                rarity_id=rarity.id,
                name_ru=f"{element.name_ru} - {template['name_ru']}",
                name_en=f"{element.name_en} - {template['name_en']}",
                generation=template["gen"],
                default_level=1,
                default_xp_for_next=100,
                description_ru=f"Спирит стихии {element.name_ru}",
                description_en=f"Spirit of {element.name_en}",
                base_run=stats["run"],
                base_jump=stats["jump"],
                base_swim=stats["swim"],
                base_dives=stats["dives"],
                base_fly=stats["fly"],
                base_maneuver=stats["maneuver"],
                base_max_energy=stats["energy"],
                icon_url=f"/icons/spirit_{element_code}_{template['suffix']}.png",
                is_starter=False,
                is_available=True,
            )
            session.add(spirit)
            spirits.append(spirit)

    await session.commit()
    print(f"✅ Создано {len(spirits)} спиритов")
    return spirits


async def seed_capsule_drops(session: AsyncSession, capsules: list, spirits: list):
    """Настройка дропов капсул (какие спириты выпадают из каких капсул)"""
    print("\n🎲 Настройка дропов капсул...")
    drops = []

    # Группируем спиритов по элементу и редкости
    spirits_by_element = {}
    for spirit in spirits:
        key = (spirit.element_id, spirit.rarity_id)
        if key not in spirits_by_element:
            spirits_by_element[key] = []
        spirits_by_element[key].append(spirit)

    # Для каждой капсулы настраиваем дропы
    for capsule in capsules:
        # Спириты того же элемента и редкости (или ниже)
        for spirit in spirits:
            if spirit.element_id == capsule.element_id:
                # Можно получить спириты той же или меньшей редкости
                if spirit.rarity_id <= capsule.rarity_id:
                    # Вес зависит от редкости (чем выше редкость, тем меньше вес)
                    weight = 100 - (spirit.rarity_id - 1) * 20  # 100, 80, 60, 40, 20

                    drop = CapsuleDrop(
                        capsule_id=capsule.id,
                        spirit_template_id=spirit.id,
                        weight=weight
                    )
                    session.add(drop)
                    drops.append(drop)

    await session.commit()
    print(f"✅ Создано {len(drops)} дропов")


async def seed_boosts(session: AsyncSession):
    """Создание шаблонов бустов"""
    print("\n⚡ Создание бустов...")
    boosts_data = [
        {
            "internal_name": "xp_small",
            "name_ru": "Малый буст опыта",
            "name_en": "Small XP Boost",
            "description_ru": "Даёт 100 опыта",
            "description_en": "Gives 100 XP",
            "price_ton": Decimal("0.1"),
            "boost_xp": 100,
            "icon_url": "/icons/boost_xp_small.png",
            "sort_order": 1,
        },
        {
            "internal_name": "xp_medium",
            "name_ru": "Средний буст опыта",
            "name_en": "Medium XP Boost",
            "description_ru": "Даёт 500 опыта",
            "description_en": "Gives 500 XP",
            "price_ton": Decimal("0.4"),
            "boost_xp": 500,
            "icon_url": "/icons/boost_xp_medium.png",
            "sort_order": 2,
        },
        {
            "internal_name": "xp_large",
            "name_ru": "Большой буст опыта",
            "name_en": "Large XP Boost",
            "description_ru": "Даёт 1500 опыта",
            "description_en": "Gives 1500 XP",
            "price_ton": Decimal("1.0"),
            "boost_xp": 1500,
            "icon_url": "/icons/boost_xp_large.png",
            "sort_order": 3,
        },
    ]

    boosts = []
    for data in boosts_data:
        boost = BoostTemplate(**data)
        session.add(boost)
        boosts.append(boost)

    await session.commit()
    print(f"✅ Создано {len(boosts)} бустов")


async def seed_slots(session: AsyncSession, elements: dict):
    """Создание шаблонов слотов"""
    print("\n🎯 Создание слотов...")
    slots = []

    for element_code, element in elements.items():
        # Стартовый слот (бесплатный)
        starter_slot = SlotTemplate(
            element_id=element.id,
            price_lumens=Decimal("0"),
            sell_price_lumens=Decimal("0"),
            is_starter=True,
            icon_url=f"/icons/slot_{element_code}_starter.png",
            is_available=False,  # Не продаётся, даётся при регистрации
        )
        session.add(starter_slot)
        slots.append(starter_slot)

        # Дополнительный слот (покупка за Lumens)
        extra_slot = SlotTemplate(
            element_id=element.id,
            price_lumens=Decimal("1000"),
            sell_price_lumens=Decimal("500"),  # Возврат 50%
            is_starter=False,
            icon_url=f"/icons/slot_{element_code}.png",
            is_available=True,
        )
        session.add(extra_slot)
        slots.append(extra_slot)

    await session.commit()
    print(f"✅ Создано {len(slots)} слотов")


async def main():
    """Главная функция seed"""
    print("🌱 Запуск seed скрипта...")

    # Создаем async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Опционально: очистка данных
        # await clear_all_data(session)

        # Seed в правильном порядке (из-за FK)
        elements = await seed_elements(session)
        rarities = await seed_rarities(session)
        capsules = await seed_capsules(session, elements, rarities)
        spirits = await seed_spirits(session, elements, rarities, capsules)
        await seed_capsule_drops(session, capsules, spirits)
        await seed_boosts(session)
        await seed_slots(session, elements)

    print("\n✅ Seed завершен успешно!")
    print("\n📊 Статистика:")
    print(f"   - Элементов: {len(elements)}")
    print(f"   - Редкостей: {len(rarities)}")
    print(f"   - Капсул: {len(capsules)}")
    print(f"   - Спиритов: {len(spirits)}")
    print(f"   - Бустов: 3")
    print(f"   - Слотов: {len(elements) * 2}")


if __name__ == "__main__":
    asyncio.run(main())
