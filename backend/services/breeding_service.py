"""
Сервис для breeding спиритов
"""
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from backend.db.models.spirit import PlayerSpirit, SpiritTemplate
from backend.db.repository import spirit as spirit_repo


# Минимальные статы по поколениям (из CLAUDE.md)
MIN_STATS_BY_GENERATION = {
    1: {"run": 1, "jump": 1, "swim": 1, "dives": 1, "fly": 1, "maneuver": 1},
    2: {"run": 3, "jump": 3, "swim": 3, "dives": 3, "fly": 3, "maneuver": 3},
    3: {"run": 5, "jump": 5, "swim": 5, "dives": 5, "fly": 5, "maneuver": 5},
    4: {"run": 8, "jump": 8, "swim": 8, "dives": 8, "fly": 8, "maneuver": 8},
    5: {"run": 10, "jump": 10, "swim": 10, "dives": 10, "fly": 10, "maneuver": 10},
    6: {"run": 12, "jump": 12, "swim": 12, "dives": 12, "fly": 12, "maneuver": 12},
    7: {"run": 15, "jump": 15, "swim": 15, "dives": 15, "fly": 15, "maneuver": 15},
}

# Стоимость breeding по поколениям (в TON)
BREEDING_COST_BY_GENERATION = {
    1: Decimal("0.1"),
    2: Decimal("0.2"),
    3: Decimal("0.3"),
    4: Decimal("0.5"),
    5: Decimal("0.8"),
    6: Decimal("1.2"),
    7: Decimal("2.0"),
}


async def validate_breeding_parents(
    db: AsyncSession,
    parent1: PlayerSpirit,
    parent2: PlayerSpirit,
    owner_id: int
) -> Dict[str, any]:
    """
    Валидирует родителей для breeding

    Проверки:
    1. Оба принадлежат текущему пользователю
    2. Одинаковый element_id
    3. Одинаковый spirit_template_id
    4. Оба level == 10
    5. Не смитнчены (можно breeding и NFT)

    Returns:
        {"valid": bool, "error": str или None}
    """
    # Проверка ownership
    if parent1.owner_id != owner_id or parent2.owner_id != owner_id:
        return {"valid": False, "error": "You don't own both spirits"}

    # Проверка одинакового spirit_template_id
    if parent1.spirit_template_id != parent2.spirit_template_id:
        return {"valid": False, "error": "Parents must be of the same spirit template"}

    # Получаем templates для проверки element_id
    template1 = parent1.template
    template2 = parent2.template

    if not template1 or not template2:
        template1 = await spirit_repo.get_spirit_template(db, parent1.spirit_template_id)
        template2 = await spirit_repo.get_spirit_template(db, parent2.spirit_template_id)

    # Проверка одинакового element_id
    if template1.element_id != template2.element_id:
        return {"valid": False, "error": "Parents must be of the same element"}

    # Проверка level == 10
    if parent1.level != 10:
        return {"valid": False, "error": f"Parent 1 must be level 10 (current: {parent1.level})"}

    if parent2.level != 10:
        return {"valid": False, "error": f"Parent 2 must be level 10 (current: {parent2.level})"}

    return {"valid": True, "error": None}


def calculate_child_stats(
    parent1: PlayerSpirit,
    parent2: PlayerSpirit
) -> Dict[str, int]:
    """
    Вычисляет статы потомка по формулам из CLAUDE.md

    Формулы:
    - child_gen = min(parent1_gen, parent2_gen) + 1
    - child_stat = max(parent1_stat, parent2_stat, MIN_STATS[gen])
    - rarity = max(parent1_rarity, parent2_rarity)

    Returns:
        {
            "generation": int,
            "base_run": int,
            "base_jump": int,
            "base_swim": int,
            "base_dives": int,
            "base_fly": int,
            "base_maneuver": int,
            "base_max_energy": int,
            "rarity_id": int
        }
    """
    # Вычисляем поколение
    child_generation = min(parent1.generation, parent2.generation) + 1
    child_generation = min(child_generation, 7)  # Максимум 7 поколение

    # Получаем минимальные статы для этого поколения
    min_stats = MIN_STATS_BY_GENERATION.get(child_generation, MIN_STATS_BY_GENERATION[7])

    # Вычисляем статы потомка
    stats = {
        "generation": child_generation,
        "base_run": max(parent1.base_run, parent2.base_run, min_stats["run"]),
        "base_jump": max(parent1.base_jump, parent2.base_jump, min_stats["jump"]),
        "base_swim": max(parent1.base_swim, parent2.base_swim, min_stats["swim"]),
        "base_dives": max(parent1.base_dives, parent2.base_dives, min_stats["dives"]),
        "base_fly": max(parent1.base_fly, parent2.base_fly, min_stats["fly"]),
        "base_maneuver": max(parent1.base_maneuver, parent2.base_maneuver, min_stats["maneuver"]),
        "base_max_energy": max(parent1.base_max_energy, parent2.base_max_energy, 100),
    }

    return stats


def get_breeding_cost(generation: int) -> Decimal:
    """
    Возвращает стоимость breeding для указанного поколения

    Args:
        generation: Поколение родителей (берем min)

    Returns:
        Decimal стоимость в TON
    """
    return BREEDING_COST_BY_GENERATION.get(generation, Decimal("2.0"))


async def breed_spirits(
    db: AsyncSession,
    parent1_id: int,
    parent2_id: int,
    owner_id: int
) -> Dict[str, any]:
    """
    Выполняет breeding двух спиритов

    Процесс:
    1. Валидация родителей
    2. Проверка баланса
    3. Вычисление статов потомка
    4. Списание TON
    5. Создание потомка
    6. Burn родителей
    7. Логирование

    Returns:
        {
            "success": bool,
            "child": PlayerSpirit или None,
            "cost": Decimal,
            "error": str или None
        }
    """
    from backend.db.repository import user as user_repo

    # Получаем родителей
    parent1 = await spirit_repo.get_player_spirit(db, parent1_id, owner_id)
    parent2 = await spirit_repo.get_player_spirit(db, parent2_id, owner_id)

    if not parent1 or not parent2:
        return {
            "success": False,
            "child": None,
            "cost": Decimal("0"),
            "error": "One or both parents not found or you don't own them"
        }

    # Валидация
    validation = await validate_breeding_parents(db, parent1, parent2, owner_id)
    if not validation["valid"]:
        return {
            "success": False,
            "child": None,
            "cost": Decimal("0"),
            "error": validation["error"]
        }

    # Вычисляем стоимость
    min_generation = min(parent1.generation, parent2.generation)
    breeding_cost = get_breeding_cost(min_generation)

    # Проверяем баланс
    user = await user_repo.get_user_by_tg_id(db, owner_id)
    if not user:
        return {
            "success": False,
            "child": None,
            "cost": breeding_cost,
            "error": "User not found"
        }

    if user.ton_balance < breeding_cost:
        return {
            "success": False,
            "child": None,
            "cost": breeding_cost,
            "error": f"Insufficient TON balance. Required: {breeding_cost}, Available: {user.ton_balance}"
        }

    # Вычисляем статы потомка
    child_stats = calculate_child_stats(parent1, parent2)

    # Получаем template для rarity_id
    parent_template = parent1.template
    if not parent_template:
        parent_template = await spirit_repo.get_spirit_template(db, parent1.spirit_template_id)

    # Rarity потомка = max rarity родителей (получаем из templates)
    # Для простоты берем rarity_id из template родителя
    child_rarity_id = parent_template.rarity_id

    try:
        async with db.begin():
            # Списываем TON
            await user_repo.subtract_balance(
                db,
                owner_id,
                breeding_cost,
                "TON",
                f"breeding_spirits_{parent1_id}_{parent2_id}"
            )

            # Создаем потомка с вычисленными статами
            child_spirit = await spirit_repo.create_player_spirit(
                db,
                owner_id=owner_id,
                spirit_template_id=parent1.spirit_template_id,
                generation=child_stats["generation"],
                level=1,
                xp=0,
                xp_for_next_level=100,
                base_run=child_stats["base_run"],
                base_jump=child_stats["base_jump"],
                base_swim=child_stats["base_swim"],
                base_dives=child_stats["base_dives"],
                base_fly=child_stats["base_fly"],
                base_maneuver=child_stats["base_maneuver"],
                base_max_energy=child_stats["base_max_energy"],
                energy=child_stats["base_max_energy"]
            )

            # Burn родителей
            # Если они смитнчены, нужно будет вызвать NFT burn (TODO: Sprint 5 NFT integration)
            if parent1.is_minted:
                # TODO: Вызвать NFT Service для burn
                pass

            if parent2.is_minted:
                # TODO: Вызвать NFT Service для burn
                pass

            # Удаляем родителей из БД
            await spirit_repo.delete_player_spirit(db, parent1_id)
            await spirit_repo.delete_player_spirit(db, parent2_id)

        await db.commit()

        return {
            "success": True,
            "child": child_spirit,
            "cost": breeding_cost,
            "error": None
        }

    except Exception as e:
        await db.rollback()
        return {
            "success": False,
            "child": None,
            "cost": breeding_cost,
            "error": f"Failed to breed spirits: {str(e)}"
        }
