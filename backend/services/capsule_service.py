"""
Сервис для работы с капсулами - открытие, weighted random и т.д.
"""
import random
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models.capsule import CapsuleDrop, CapsuleTemplate
from backend.db.models.spirit import SpiritTemplate


async def get_weighted_random_spirit(
    db: AsyncSession, capsule_template_id: int
) -> Optional[SpiritTemplate]:
    """
    Выбирает случайный спирит из доступных дропов для капсулы
    используя weighted random

    Returns:
        SpiritTemplate или None если нет доступных дропов
    """
    # Получаем все доступные дропы для этой капсулы
    result = await db.execute(
        select(CapsuleDrop)
        .where(CapsuleDrop.capsule_id == capsule_template_id)
        .options(selectinload(CapsuleDrop.spirit_template))
    )
    drops = list(result.scalars().all())

    if not drops:
        return None

    # Создаем список спиритов и весов
    spirits = []
    weights = []

    for drop in drops:
        if drop.spirit_template and drop.spirit_template.is_available:
            spirits.append(drop.spirit_template)
            weights.append(drop.weight)

    if not spirits:
        return None

    # Используем random.choices для weighted random выбора
    selected_spirit = random.choices(spirits, weights=weights, k=1)[0]

    return selected_spirit


async def validate_capsule_spirit_rarity(
    db: AsyncSession,
    capsule_template: CapsuleTemplate,
    spirit_template: SpiritTemplate
) -> bool:
    """
    Проверяет, что rarity спирита <= rarity капсулы

    Returns:
        True если валидация пройдена, False иначе
    """
    # Получаем rarity_id капсулы и спирита
    capsule_rarity = capsule_template.rarity_id
    spirit_rarity = spirit_template.rarity_id

    # Проверяем, что rarity спирита не выше rarity капсулы
    # Предполагаем, что rarity_id увеличивается с редкостью (1=common, 5=mythical)
    return spirit_rarity <= capsule_rarity


async def open_capsule_synchronous(
    db: AsyncSession,
    player_capsule_id: int,
    owner_id: int
) -> dict:
    """
    Синхронное открытие капсулы (для капсул с open_time_seconds = 0)

    Возвращает:
        {
            "success": bool,
            "spirit": PlayerSpirit или None,
            "error": str или None
        }
    """
    from backend.db.repository import capsule as capsule_repo
    from backend.db.repository import spirit as spirit_repo

    # Получаем капсулу игрока
    player_capsule = await capsule_repo.get_player_capsule(db, player_capsule_id, owner_id)

    if not player_capsule:
        return {
            "success": False,
            "spirit": None,
            "error": "Capsule not found or you don't own it"
        }

    if player_capsule.is_opened:
        return {
            "success": False,
            "spirit": None,
            "error": "Capsule is already opened"
        }

    if player_capsule.quantity <= 0:
        return {
            "success": False,
            "spirit": None,
            "error": "No capsules to open"
        }

    # Получаем шаблон капсулы
    capsule_template = player_capsule.template
    if not capsule_template:
        capsule_template = await capsule_repo.get_capsule_template(db, player_capsule.capsule_id)

    # Выбираем случайный спирит через weighted random
    spirit_template = await get_weighted_random_spirit(db, capsule_template.id)

    if not spirit_template:
        return {
            "success": False,
            "spirit": None,
            "error": "No available spirits for this capsule"
        }

    # Проверяем rarity constraint
    if not await validate_capsule_spirit_rarity(db, capsule_template, spirit_template):
        return {
            "success": False,
            "spirit": None,
            "error": "Spirit rarity exceeds capsule rarity"
        }

    try:
        async with db.begin():
            # Создаем спирита для игрока
            player_spirit = await spirit_repo.create_player_spirit(
                db,
                owner_id,
                spirit_template.id,
                generation=spirit_template.generation,
                level=spirit_template.default_level
            )

            # Уменьшаем количество капсул
            await capsule_repo.update_player_capsule_quantity(
                db, player_capsule_id, player_capsule.quantity - 1
            )

        await db.commit()

        return {
            "success": True,
            "spirit": player_spirit,
            "error": None
        }

    except Exception as e:
        await db.rollback()
        return {
            "success": False,
            "spirit": None,
            "error": f"Failed to open capsule: {str(e)}"
        }
