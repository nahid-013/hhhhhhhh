"""
Repository для работы с боевой системой
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models.battle import BattleSession, BattlePlayer
from backend.schemas.battle import (
    BattleSessionCreate, BattleSessionUpdate,
    BattlePlayerCreate, BattlePlayerUpdate
)


# ===================== BattleSession CRUD =====================

async def create_battle_session(
    db: AsyncSession, session_data: BattleSessionCreate
) -> BattleSession:
    """Создать новую сессию боя"""
    db_session = BattleSession(
        mode=session_data.mode,
        created_by=session_data.created_by,
        seed=session_data.seed,
        started_at=datetime.utcnow()
    )
    db.add(db_session)
    await db.flush()
    await db.refresh(db_session)
    return db_session


async def get_battle_session(
    db: AsyncSession, session_id: int
) -> Optional[BattleSession]:
    """Получить сессию боя по ID"""
    result = await db.execute(
        select(BattleSession)
        .where(BattleSession.id == session_id)
        .options(
            selectinload(BattleSession.players),
            selectinload(BattleSession.creator)
        )
    )
    return result.scalar_one_or_none()


async def get_battle_sessions_by_player(
    db: AsyncSession,
    player_id: int,
    mode: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[List[BattleSession], int]:
    """Получить список боев игрока с пагинацией"""
    # Базовый запрос для подсчета
    count_query = (
        select(func.count(BattleSession.id))
        .join(BattlePlayer, BattlePlayer.battle_session_id == BattleSession.id)
        .where(BattlePlayer.player_id == player_id)
    )

    # Базовый запрос для получения данных
    query = (
        select(BattleSession)
        .join(BattlePlayer, BattlePlayer.battle_session_id == BattleSession.id)
        .where(BattlePlayer.player_id == player_id)
    )

    if mode:
        count_query = count_query.where(BattleSession.mode == mode)
        query = query.where(BattleSession.mode == mode)

    # Получить общее количество
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Получить данные с пагинацией
    query = (
        query.options(selectinload(BattleSession.players))
        .order_by(desc(BattleSession.started_at))
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    sessions = list(result.scalars().unique().all())

    return sessions, total


async def update_battle_session(
    db: AsyncSession, session_id: int, session_data: BattleSessionUpdate
) -> Optional[BattleSession]:
    """Обновить сессию боя"""
    update_data = session_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_battle_session(db, session_id)

    await db.execute(
        update(BattleSession)
        .where(BattleSession.id == session_id)
        .values(**update_data)
    )
    await db.flush()
    return await get_battle_session(db, session_id)


async def finish_battle_session(
    db: AsyncSession, session_id: int, result_json: dict
) -> Optional[BattleSession]:
    """Завершить сессию боя"""
    await db.execute(
        update(BattleSession)
        .where(BattleSession.id == session_id)
        .values(
            finished_at=datetime.utcnow(),
            result_json=result_json
        )
    )
    await db.flush()
    return await get_battle_session(db, session_id)


# ===================== BattlePlayer CRUD =====================

async def create_battle_player(
    db: AsyncSession, player_data: BattlePlayerCreate
) -> BattlePlayer:
    """Создать участника боя"""
    db_player = BattlePlayer(**player_data.model_dump())
    db.add(db_player)
    await db.flush()
    await db.refresh(db_player)
    return db_player


async def create_battle_players_bulk(
    db: AsyncSession, players_data: List[BattlePlayerCreate]
) -> List[BattlePlayer]:
    """Создать нескольких участников боя (bulk insert)"""
    db_players = [BattlePlayer(**player.model_dump()) for player in players_data]
    db.add_all(db_players)
    await db.flush()
    for player in db_players:
        await db.refresh(player)
    return db_players


async def get_battle_player(
    db: AsyncSession, player_id: int
) -> Optional[BattlePlayer]:
    """Получить участника боя по ID"""
    result = await db.execute(
        select(BattlePlayer)
        .where(BattlePlayer.id == player_id)
        .options(
            selectinload(BattlePlayer.player),
            selectinload(BattlePlayer.spirit),
            selectinload(BattlePlayer.session)
        )
    )
    return result.scalar_one_or_none()


async def get_battle_players_by_session(
    db: AsyncSession, session_id: int
) -> List[BattlePlayer]:
    """Получить всех участников боя"""
    result = await db.execute(
        select(BattlePlayer)
        .where(BattlePlayer.battle_session_id == session_id)
        .options(
            selectinload(BattlePlayer.player),
            selectinload(BattlePlayer.spirit)
        )
        .order_by(BattlePlayer.rank)
    )
    return list(result.scalars().all())


async def update_battle_player(
    db: AsyncSession, player_id: int, player_data: BattlePlayerUpdate
) -> Optional[BattlePlayer]:
    """Обновить результаты участника боя"""
    update_data = player_data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_battle_player(db, player_id)

    await db.execute(
        update(BattlePlayer)
        .where(BattlePlayer.id == player_id)
        .values(**update_data)
    )
    await db.flush()
    return await get_battle_player(db, player_id)


async def update_battle_players_results(
    db: AsyncSession, results: List[dict]
) -> None:
    """
    Обновить результаты всех участников боя (bulk update)

    Args:
        results: Список словарей с ключами: id, score, distance, rank, xp_earned, lumens_earned, capsule_reward_id
    """
    for result in results:
        player_id = result.pop('id')
        await db.execute(
            update(BattlePlayer)
            .where(BattlePlayer.id == player_id)
            .values(**result)
        )
    await db.flush()


# ===================== Статистика и аналитика =====================

async def get_player_battle_stats(
    db: AsyncSession, player_id: int
) -> dict:
    """Получить статистику боев игрока"""
    # Общее количество боев
    total_query = select(func.count(BattlePlayer.id)).where(
        BattlePlayer.player_id == player_id
    )
    total_result = await db.execute(total_query)
    total_battles = total_result.scalar_one()

    # Количество побед (rank == 1)
    wins_query = select(func.count(BattlePlayer.id)).where(
        BattlePlayer.player_id == player_id,
        BattlePlayer.rank == 1
    )
    wins_result = await db.execute(wins_query)
    wins = wins_result.scalar_one()

    # Общий заработок XP
    xp_query = select(func.sum(BattlePlayer.xp_earned)).where(
        BattlePlayer.player_id == player_id
    )
    xp_result = await db.execute(xp_query)
    total_xp = xp_result.scalar_one() or 0

    # Общий заработок Lumens
    lumens_query = select(func.sum(BattlePlayer.lumens_earned)).where(
        BattlePlayer.player_id == player_id
    )
    lumens_result = await db.execute(lumens_query)
    total_lumens = lumens_result.scalar_one() or 0

    return {
        'total_battles': total_battles,
        'wins': wins,
        'win_rate': wins / total_battles if total_battles > 0 else 0.0,
        'total_xp_earned': int(total_xp),
        'total_lumens_earned': int(total_lumens)
    }


async def get_top_players_by_wins(
    db: AsyncSession, limit: int = 100
) -> List[dict]:
    """Получить топ игроков по количеству побед"""
    query = (
        select(
            BattlePlayer.player_id,
            func.count(BattlePlayer.id).label('total_battles'),
            func.sum(func.case((BattlePlayer.rank == 1, 1), else_=0)).label('wins')
        )
        .group_by(BattlePlayer.player_id)
        .order_by(desc('wins'))
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            'player_id': row.player_id,
            'total_battles': row.total_battles,
            'wins': row.wins,
            'win_rate': row.wins / row.total_battles if row.total_battles > 0 else 0.0
        }
        for row in rows
    ]


async def get_recent_battles(
    db: AsyncSession, limit: int = 10
) -> List[BattleSession]:
    """Получить недавние завершенные бои"""
    result = await db.execute(
        select(BattleSession)
        .where(BattleSession.finished_at.isnot(None))
        .options(selectinload(BattleSession.players))
        .order_by(desc(BattleSession.finished_at))
        .limit(limit)
    )
    return list(result.scalars().all())
