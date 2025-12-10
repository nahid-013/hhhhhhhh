"""
Repository для работы со слотами
"""
from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models.slot import SlotTemplate, PlayerSlot
from backend.schemas.slot import SlotTemplateCreate, SlotTemplateUpdate


async def get_slot_template(db: AsyncSession, slot_id: int) -> Optional[SlotTemplate]:
    """Получить шаблон слота по ID"""
    result = await db.execute(
        select(SlotTemplate).where(SlotTemplate.id == slot_id)
    )
    return result.scalar_one_or_none()


async def get_slot_templates(
    db: AsyncSession,
    element_id: Optional[int] = None,
    is_available: bool = True,
) -> List[SlotTemplate]:
    """Получить список шаблонов слотов с фильтрами"""
    query = select(SlotTemplate).where(SlotTemplate.is_available == is_available)

    if element_id:
        query = query.where(SlotTemplate.element_id == element_id)

    result = await db.execute(query.order_by(SlotTemplate.id))
    return list(result.scalars().all())


async def create_slot_template(
    db: AsyncSession, slot_data: SlotTemplateCreate
) -> SlotTemplate:
    """Создать новый шаблон слота (admin)"""
    db_slot = SlotTemplate(**slot_data.model_dump())
    db.add(db_slot)
    await db.flush()
    await db.refresh(db_slot)
    return db_slot


async def update_slot_template(
    db: AsyncSession, slot_id: int, slot_data: SlotTemplateUpdate
) -> Optional[SlotTemplate]:
    """Обновить шаблон слота (admin)"""
    update_data = slot_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_slot_template(db, slot_id)

    await db.execute(
        update(SlotTemplate)
        .where(SlotTemplate.id == slot_id)
        .values(**update_data)
    )
    return await get_slot_template(db, slot_id)


async def delete_slot_template(db: AsyncSession, slot_id: int) -> bool:
    """Удалить шаблон слота (admin)"""
    result = await db.execute(
        delete(SlotTemplate).where(SlotTemplate.id == slot_id)
    )
    return result.rowcount > 0


# Player Slots
async def get_player_slot(
    db: AsyncSession, player_slot_id: int, owner_id: Optional[int] = None
) -> Optional[PlayerSlot]:
    """Получить слот игрока"""
    query = select(PlayerSlot).where(PlayerSlot.id == player_slot_id)
    if owner_id:
        query = query.where(PlayerSlot.owner_id == owner_id)

    result = await db.execute(
        query.options(
            selectinload(PlayerSlot.template),
            selectinload(PlayerSlot.element),
            selectinload(PlayerSlot.spirit)
        )
    )
    return result.scalar_one_or_none()


async def get_player_slots(db: AsyncSession, owner_id: int) -> List[PlayerSlot]:
    """Получить все слоты игрока (партию)"""
    result = await db.execute(
        select(PlayerSlot)
        .where(PlayerSlot.owner_id == owner_id)
        .options(
            selectinload(PlayerSlot.template),
            selectinload(PlayerSlot.element),
            selectinload(PlayerSlot.spirit)
        )
        .order_by(PlayerSlot.acquired_at.desc())
    )
    return list(result.scalars().all())


async def create_player_slot(
    db: AsyncSession,
    owner_id: int,
    slot_template_id: int,
    element_id: int,
) -> PlayerSlot:
    """Создать слот для игрока"""
    db_player_slot = PlayerSlot(
        owner_id=owner_id,
        slot_template_id=slot_template_id,
        element_id=element_id,
    )
    db.add(db_player_slot)
    await db.flush()
    await db.refresh(db_player_slot)
    return db_player_slot


async def delete_player_slot(db: AsyncSession, player_slot_id: int) -> bool:
    """Удалить слот игрока (продажа)"""
    result = await db.execute(
        delete(PlayerSlot).where(PlayerSlot.id == player_slot_id)
    )
    return result.rowcount > 0


async def count_player_slots(db: AsyncSession, owner_id: int) -> int:
    """Подсчитать количество слотов у игрока"""
    result = await db.execute(
        select(PlayerSlot).where(PlayerSlot.owner_id == owner_id)
    )
    return len(list(result.scalars().all()))


async def get_starter_slot_templates(db: AsyncSession) -> List[SlotTemplate]:
    """Получить все стартовые шаблоны слотов (is_starter=True)"""
    result = await db.execute(
        select(SlotTemplate)
        .where(SlotTemplate.is_starter == True)
        .options(selectinload(SlotTemplate.element))
    )
    return list(result.scalars().all())


async def create_starter_slots_for_user(db: AsyncSession, user_id: int) -> List[PlayerSlot]:
    """
    Создать стартовые слоты для нового пользователя

    Выдает по одному слоту для каждого элемента (всего 6 слотов)

    Args:
        db: AsyncSession для работы с БД
        user_id: tg_id пользователя

    Returns:
        List[PlayerSlot]: Список созданных слотов
    """
    # Получаем все стартовые шаблоны слотов
    starter_templates = await get_starter_slot_templates(db)

    if not starter_templates:
        # Если нет стартовых шаблонов, логируем предупреждение
        # В production это должно быть решено через seed данные
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"No starter slot templates found for user {user_id}")
        return []

    # Создаем слот для каждого стартового шаблона
    created_slots = []
    for template in starter_templates:
        player_slot = await create_player_slot(
            db=db,
            owner_id=user_id,
            slot_template_id=template.id,
            element_id=template.element_id,
        )
        created_slots.append(player_slot)

    return created_slots
