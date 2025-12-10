"""
Repository для работы со спиритами
"""
from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models.spirit import SpiritTemplate, PlayerSpirit
from backend.schemas.spirit import SpiritTemplateCreate, SpiritTemplateUpdate


async def get_spirit_template(db: AsyncSession, spirit_id: int) -> Optional[SpiritTemplate]:
    """Получить шаблон спирита по ID"""
    result = await db.execute(
        select(SpiritTemplate)
        .where(SpiritTemplate.id == spirit_id)
        .options(
            selectinload(SpiritTemplate.element),
            selectinload(SpiritTemplate.rarity),
            selectinload(SpiritTemplate.capsule)
        )
    )
    return result.scalar_one_or_none()


async def get_spirit_template_by_code(db: AsyncSession, code: str) -> Optional[SpiritTemplate]:
    """Получить шаблон спирита по коду"""
    result = await db.execute(
        select(SpiritTemplate).where(SpiritTemplate.code == code)
    )
    return result.scalar_one_or_none()


async def get_spirit_templates(
    db: AsyncSession,
    element_id: Optional[int] = None,
    rarity_id: Optional[int] = None,
    generation: Optional[int] = None,
    is_available: bool = True,
) -> List[SpiritTemplate]:
    """Получить список шаблонов спиритов с фильтрами"""
    query = select(SpiritTemplate).where(SpiritTemplate.is_available == is_available)

    if element_id:
        query = query.where(SpiritTemplate.element_id == element_id)
    if rarity_id:
        query = query.where(SpiritTemplate.rarity_id == rarity_id)
    if generation:
        query = query.where(SpiritTemplate.generation == generation)

    result = await db.execute(
        query.options(
            selectinload(SpiritTemplate.element),
            selectinload(SpiritTemplate.rarity)
        ).order_by(SpiritTemplate.id)
    )
    return list(result.scalars().all())


async def create_spirit_template(
    db: AsyncSession, spirit_data: SpiritTemplateCreate
) -> SpiritTemplate:
    """Создать новый шаблон спирита (admin)"""
    db_spirit = SpiritTemplate(**spirit_data.model_dump())
    db.add(db_spirit)
    await db.flush()
    await db.refresh(db_spirit)
    return db_spirit


async def update_spirit_template(
    db: AsyncSession, spirit_id: int, spirit_data: SpiritTemplateUpdate
) -> Optional[SpiritTemplate]:
    """Обновить шаблон спирита (admin)"""
    update_data = spirit_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_spirit_template(db, spirit_id)

    await db.execute(
        update(SpiritTemplate)
        .where(SpiritTemplate.id == spirit_id)
        .values(**update_data)
    )
    return await get_spirit_template(db, spirit_id)


async def delete_spirit_template(db: AsyncSession, spirit_id: int) -> bool:
    """Удалить шаблон спирита (admin)"""
    result = await db.execute(
        delete(SpiritTemplate).where(SpiritTemplate.id == spirit_id)
    )
    return result.rowcount > 0


# Player Spirits
async def get_player_spirit(
    db: AsyncSession, player_spirit_id: int, owner_id: Optional[int] = None
) -> Optional[PlayerSpirit]:
    """Получить спирита игрока"""
    query = select(PlayerSpirit).where(PlayerSpirit.id == player_spirit_id)
    if owner_id:
        query = query.where(PlayerSpirit.owner_id == owner_id)

    result = await db.execute(
        query.options(
            selectinload(PlayerSpirit.template),
            selectinload(PlayerSpirit.slot)
        )
    )
    return result.scalar_one_or_none()


async def get_player_spirits(
    db: AsyncSession,
    owner_id: int,
    is_active: Optional[bool] = None,
) -> List[PlayerSpirit]:
    """Получить всех спиритов игрока"""
    query = select(PlayerSpirit).where(PlayerSpirit.owner_id == owner_id)

    if is_active is not None:
        query = query.where(PlayerSpirit.is_active == is_active)

    result = await db.execute(
        query.options(
            selectinload(PlayerSpirit.template),
            selectinload(PlayerSpirit.slot)
        ).order_by(PlayerSpirit.acquired_at.desc())
    )
    return list(result.scalars().all())


async def create_player_spirit(
    db: AsyncSession,
    owner_id: int,
    spirit_template_id: int,
    generation: int = 1,
    level: int = 1,
    **kwargs
) -> PlayerSpirit:
    """
    Создать спирита для игрока
    kwargs может содержать: custom_name, base_stats, energy и т.д.
    """
    # Получаем шаблон для копирования базовых характеристик
    template = await get_spirit_template(db, spirit_template_id)
    if not template:
        raise ValueError(f"Spirit template {spirit_template_id} not found")

    spirit_data = {
        "owner_id": owner_id,
        "spirit_template_id": spirit_template_id,
        "generation": generation,
        "level": level,
        "xp": 0,
        "xp_for_next_level": 100,
        # Копируем базовые характеристики из template
        "base_run": template.base_run,
        "base_jump": template.base_jump,
        "base_swim": template.base_swim,
        "base_dives": template.base_dives,
        "base_fly": template.base_fly,
        "base_maneuver": template.base_maneuver,
        "base_max_energy": template.base_max_energy,
        "energy": template.base_max_energy,
    }

    # Переопределяем значениями из kwargs если они есть
    spirit_data.update(kwargs)

    db_player_spirit = PlayerSpirit(**spirit_data)
    db.add(db_player_spirit)
    await db.flush()
    await db.refresh(db_player_spirit)
    return db_player_spirit


async def update_player_spirit(
    db: AsyncSession, player_spirit_id: int, **kwargs
) -> Optional[PlayerSpirit]:
    """Обновить спирита игрока"""
    if not kwargs:
        return await get_player_spirit(db, player_spirit_id)

    await db.execute(
        update(PlayerSpirit)
        .where(PlayerSpirit.id == player_spirit_id)
        .values(**kwargs)
    )
    return await get_player_spirit(db, player_spirit_id)


async def delete_player_spirit(db: AsyncSession, player_spirit_id: int) -> bool:
    """Удалить спирита игрока (burn)"""
    result = await db.execute(
        delete(PlayerSpirit).where(PlayerSpirit.id == player_spirit_id)
    )
    return result.rowcount > 0


async def activate_spirit(
    db: AsyncSession, player_spirit_id: int, slot_id: int
) -> Optional[PlayerSpirit]:
    """Активировать спирита в слоте"""
    await db.execute(
        update(PlayerSpirit)
        .where(PlayerSpirit.id == player_spirit_id)
        .values(is_active=True, slot_id=slot_id)
    )
    return await get_player_spirit(db, player_spirit_id)


async def deactivate_spirit(db: AsyncSession, player_spirit_id: int) -> Optional[PlayerSpirit]:
    """Деактивировать спирита"""
    await db.execute(
        update(PlayerSpirit)
        .where(PlayerSpirit.id == player_spirit_id)
        .values(is_active=False, slot_id=None)
    )
    return await get_player_spirit(db, player_spirit_id)


async def get_active_spirits(db: AsyncSession, owner_id: int) -> List[PlayerSpirit]:
    """Получить активных спиритов игрока (партия)"""
    return await get_player_spirits(db, owner_id, is_active=True)


async def add_xp_to_spirit(
    db: AsyncSession, player_spirit_id: int, xp_amount: int
) -> Optional[PlayerSpirit]:
    """Добавить опыт спириту"""
    spirit = await get_player_spirit(db, player_spirit_id)
    if not spirit:
        return None

    new_xp = spirit.xp + xp_amount
    new_level = spirit.level
    xp_for_next = spirit.xp_for_next_level

    # Проверка на повышение уровня
    while new_xp >= xp_for_next:
        new_xp -= xp_for_next
        new_level += 1
        xp_for_next = int(100 * (new_level ** 1.2))  # Формула из CLAUDE.md

    await db.execute(
        update(PlayerSpirit)
        .where(PlayerSpirit.id == player_spirit_id)
        .values(xp=new_xp, level=new_level, xp_for_next_level=xp_for_next)
    )
    return await get_player_spirit(db, player_spirit_id)
