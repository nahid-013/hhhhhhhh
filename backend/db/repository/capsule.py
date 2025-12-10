"""
Repository для работы с капсулами
"""
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models.capsule import CapsuleTemplate, PlayerCapsule
from backend.schemas.capsule import CapsuleTemplateCreate, CapsuleTemplateUpdate


async def get_capsule_template(db: AsyncSession, capsule_id: int) -> Optional[CapsuleTemplate]:
    """Получить шаблон капсулы по ID"""
    result = await db.execute(
        select(CapsuleTemplate).where(CapsuleTemplate.id == capsule_id)
    )
    return result.scalar_one_or_none()


async def get_capsule_templates(
    db: AsyncSession,
    element_id: Optional[int] = None,
    rarity_id: Optional[int] = None,
    is_available: bool = True,
) -> List[CapsuleTemplate]:
    """Получить список шаблонов капсул с фильтрами"""
    query = select(CapsuleTemplate).where(CapsuleTemplate.is_available == is_available)

    if element_id:
        query = query.where(CapsuleTemplate.element_id == element_id)
    if rarity_id:
        query = query.where(CapsuleTemplate.rarity_id == rarity_id)

    result = await db.execute(query.order_by(CapsuleTemplate.id))
    return list(result.scalars().all())


async def create_capsule_template(
    db: AsyncSession, capsule_data: CapsuleTemplateCreate
) -> CapsuleTemplate:
    """Создать новый шаблон капсулы (admin)"""
    db_capsule = CapsuleTemplate(**capsule_data.model_dump())
    db.add(db_capsule)
    await db.flush()
    await db.refresh(db_capsule)
    return db_capsule


async def update_capsule_template(
    db: AsyncSession, capsule_id: int, capsule_data: CapsuleTemplateUpdate
) -> Optional[CapsuleTemplate]:
    """Обновить шаблон капсулы (admin)"""
    update_data = capsule_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_capsule_template(db, capsule_id)

    await db.execute(
        update(CapsuleTemplate)
        .where(CapsuleTemplate.id == capsule_id)
        .values(**update_data)
    )
    return await get_capsule_template(db, capsule_id)


async def delete_capsule_template(db: AsyncSession, capsule_id: int) -> bool:
    """Удалить шаблон капсулы (admin)"""
    result = await db.execute(
        delete(CapsuleTemplate).where(CapsuleTemplate.id == capsule_id)
    )
    return result.rowcount > 0


# Player Capsules
async def get_player_capsule(
    db: AsyncSession, player_capsule_id: int, owner_id: Optional[int] = None
) -> Optional[PlayerCapsule]:
    """Получить капсулу игрока"""
    query = select(PlayerCapsule).where(PlayerCapsule.id == player_capsule_id)
    if owner_id:
        query = query.where(PlayerCapsule.owner_id == owner_id)

    result = await db.execute(query.options(selectinload(PlayerCapsule.template)))
    return result.scalar_one_or_none()


async def get_player_capsules(db: AsyncSession, owner_id: int) -> List[PlayerCapsule]:
    """Получить все капсулы игрока"""
    result = await db.execute(
        select(PlayerCapsule)
        .where(PlayerCapsule.owner_id == owner_id)
        .options(selectinload(PlayerCapsule.template))
        .order_by(PlayerCapsule.acquired_at.desc())
    )
    return list(result.scalars().all())


async def create_player_capsule(
    db: AsyncSession,
    owner_id: int,
    capsule_id: int,
    quantity: int = 1,
) -> PlayerCapsule:
    """Создать капсулу для игрока"""
    db_player_capsule = PlayerCapsule(
        owner_id=owner_id,
        capsule_id=capsule_id,
        quantity=quantity,
    )
    db.add(db_player_capsule)
    await db.flush()
    await db.refresh(db_player_capsule)
    return db_player_capsule


async def update_player_capsule_quantity(
    db: AsyncSession, player_capsule_id: int, new_quantity: int
) -> Optional[PlayerCapsule]:
    """Обновить количество капсул"""
    if new_quantity <= 0:
        # Если количество стало 0 или меньше, удаляем запись
        await db.execute(
            delete(PlayerCapsule).where(PlayerCapsule.id == player_capsule_id)
        )
        return None

    await db.execute(
        update(PlayerCapsule)
        .where(PlayerCapsule.id == player_capsule_id)
        .values(quantity=new_quantity)
    )
    return await get_player_capsule(db, player_capsule_id)
