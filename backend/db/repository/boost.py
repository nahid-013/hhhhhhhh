"""
Repository для работы с бустами
"""
from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models.boost import BoostTemplate, PlayerBoost
from backend.schemas.boost import BoostTemplateCreate, BoostTemplateUpdate


async def get_boost_template(db: AsyncSession, boost_id: int) -> Optional[BoostTemplate]:
    """Получить шаблон буста по ID"""
    result = await db.execute(
        select(BoostTemplate).where(BoostTemplate.id == boost_id)
    )
    return result.scalar_one_or_none()


async def get_boost_templates(
    db: AsyncSession, is_available: bool = True
) -> List[BoostTemplate]:
    """Получить список шаблонов бустов"""
    result = await db.execute(
        select(BoostTemplate)
        .where(BoostTemplate.is_available == is_available)
        .order_by(BoostTemplate.sort_order, BoostTemplate.id)
    )
    return list(result.scalars().all())


async def create_boost_template(
    db: AsyncSession, boost_data: BoostTemplateCreate
) -> BoostTemplate:
    """Создать новый шаблон буста (admin)"""
    db_boost = BoostTemplate(**boost_data.model_dump())
    db.add(db_boost)
    await db.flush()
    await db.refresh(db_boost)
    return db_boost


async def update_boost_template(
    db: AsyncSession, boost_id: int, boost_data: BoostTemplateUpdate
) -> Optional[BoostTemplate]:
    """Обновить шаблон буста (admin)"""
    update_data = boost_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_boost_template(db, boost_id)

    await db.execute(
        update(BoostTemplate)
        .where(BoostTemplate.id == boost_id)
        .values(**update_data)
    )
    return await get_boost_template(db, boost_id)


async def delete_boost_template(db: AsyncSession, boost_id: int) -> bool:
    """Удалить шаблон буста (admin)"""
    result = await db.execute(
        delete(BoostTemplate).where(BoostTemplate.id == boost_id)
    )
    return result.rowcount > 0


# Player Boosts
async def get_player_boost(
    db: AsyncSession, player_boost_id: int, owner_id: Optional[int] = None
) -> Optional[PlayerBoost]:
    """Получить буст игрока"""
    query = select(PlayerBoost).where(PlayerBoost.id == player_boost_id)
    if owner_id:
        query = query.where(PlayerBoost.owner_id == owner_id)

    result = await db.execute(query.options(selectinload(PlayerBoost.template)))
    return result.scalar_one_or_none()


async def get_player_boosts(db: AsyncSession, owner_id: int) -> List[PlayerBoost]:
    """Получить все бусты игрока"""
    result = await db.execute(
        select(PlayerBoost)
        .where(PlayerBoost.owner_id == owner_id)
        .where(PlayerBoost.quantity > 0)
        .options(selectinload(PlayerBoost.template))
        .order_by(PlayerBoost.acquired_at.desc())
    )
    return list(result.scalars().all())


async def create_player_boost(
    db: AsyncSession,
    owner_id: int,
    boost_id: int,
    quantity: int = 1,
) -> PlayerBoost:
    """Создать буст для игрока"""
    db_player_boost = PlayerBoost(
        owner_id=owner_id,
        boost_id=boost_id,
        quantity=quantity,
    )
    db.add(db_player_boost)
    await db.flush()
    await db.refresh(db_player_boost)
    return db_player_boost


async def update_player_boost_quantity(
    db: AsyncSession, player_boost_id: int, new_quantity: int
) -> Optional[PlayerBoost]:
    """Обновить количество бустов"""
    if new_quantity <= 0:
        # Если количество стало 0 или меньше, удаляем запись
        await db.execute(
            delete(PlayerBoost).where(PlayerBoost.id == player_boost_id)
        )
        return None

    await db.execute(
        update(PlayerBoost)
        .where(PlayerBoost.id == player_boost_id)
        .values(quantity=new_quantity)
    )
    return await get_player_boost(db, player_boost_id)


async def get_or_create_player_boost(
    db: AsyncSession, owner_id: int, boost_id: int, quantity: int = 1
) -> PlayerBoost:
    """Получить или создать буст игрока (для покупки)"""
    # Проверяем, есть ли уже такой буст у игрока
    result = await db.execute(
        select(PlayerBoost)
        .where(PlayerBoost.owner_id == owner_id)
        .where(PlayerBoost.boost_id == boost_id)
    )
    player_boost = result.scalar_one_or_none()

    if player_boost:
        # Если есть, увеличиваем количество
        player_boost.quantity += quantity
        await db.flush()
        await db.refresh(player_boost)
        return player_boost
    else:
        # Если нет, создаём новый
        return await create_player_boost(db, owner_id, boost_id, quantity)
