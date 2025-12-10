"""
API эндпоинты для боевой системы
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import secrets

from backend.db.session import get_db
from backend.schemas.battle import (
    BattleFullResponse,
    BattleHistoryRequest,
    BattleHistoryResponse,
    BattleHistoryItem,
    BattleSessionCreate,
    BattlePlayerCreate,
    BattleSessionUpdate,
)
from backend.db.repository import battle as battle_repo
from backend.db.repository import spirit as spirit_repo
from backend.core.security import get_current_user_id
from backend.services.battle.engine import BattleSimulator, SpiritStats
from backend.services.battle.rewards import RewardsService


router = APIRouter()


async def get_spirit_stats_for_battle(db: AsyncSession, spirit_id: int) -> Optional[SpiritStats]:
    """Получить статы спирита для боя"""
    spirit = await spirit_repo.get_player_spirit(db, spirit_id)

    if not spirit:
        return None

    # Получить rarity factor
    rarity_factors = {
        1: 1.0,   # common
        2: 1.2,   # rare
        3: 1.5,   # epic
        4: 2.0,   # legendary
        5: 2.5,   # mythical
    }

    rarity_id = spirit.template.rarity_id if spirit.template else 1
    rarity_factor = rarity_factors.get(rarity_id, 1.0)

    return SpiritStats(
        spirit_id=spirit.id,
        player_id=spirit.owner_id,
        base_run=spirit.base_run,
        base_jump=spirit.base_jump,
        base_swim=spirit.base_swim,
        base_dives=spirit.base_dives,
        base_fly=spirit.base_fly,
        base_maneuver=spirit.base_maneuver,
        level=spirit.level,
        rarity_factor=rarity_factor
    )


@router.post("/battles/start", response_model=dict)
async def start_battle(
    mode: str,
    player_ids: List[int],
    spirit_ids: List[int],
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Запустить новый бой (внутренний endpoint, вызывается после matchmaking)

    Для тестирования можно вызвать вручную с 3 игроками
    """
    if len(player_ids) != 3 or len(spirit_ids) != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Battle requires exactly 3 players"
        )

    # Проверить, что текущий пользователь - один из участников
    if current_user_id not in player_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant"
        )

    # Получить статы всех спиритов
    spirits_stats = []
    for i, spirit_id in enumerate(spirit_ids):
        stats = await get_spirit_stats_for_battle(db, spirit_id)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Spirit {spirit_id} not found"
            )

        # Проверить ownership
        if stats.player_id != player_ids[i]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Spirit {spirit_id} does not belong to player {player_ids[i]}"
            )

        spirits_stats.append(stats)

    # Создать battle session
    seed = secrets.randbelow(2**31)

    session_data = BattleSessionCreate(
        mode=mode,
        created_by=current_user_id,
        seed=seed
    )

    battle_session = await battle_repo.create_battle_session(db, session_data)

    # Создать battle players
    players_data = []
    for i, (player_id, spirit_id) in enumerate(zip(player_ids, spirit_ids)):
        stats = spirits_stats[i]

        player_data = BattlePlayerCreate(
            battle_session_id=battle_session.id,
            player_id=player_id,
            player_spirit_id=spirit_id,
            stats_snapshot={
                'base_run': stats.base_run,
                'base_jump': stats.base_jump,
                'base_swim': stats.base_swim,
                'base_dives': stats.base_dives,
                'base_fly': stats.base_fly,
                'base_maneuver': stats.base_maneuver,
                'level': stats.level,
                'rarity_factor': stats.rarity_factor
            }
        )
        players_data.append(player_data)

    battle_players = await battle_repo.create_battle_players_bulk(db, players_data)

    # Списать энергию у всех спиритов
    rewards_service = RewardsService(db)

    for spirit_id in spirit_ids:
        try:
            await rewards_service.deduct_energy(spirit_id, amount=15)
        except ValueError as e:
            # Откатить транзакцию
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    # Запустить симуляцию
    simulator = BattleSimulator(seed)
    results, replay_data = simulator.simulate_flow_flight(spirits_stats)

    # Рассчитать награды
    rewards = simulator.calculate_rewards(results)

    # Обновить результаты battle_players
    player_updates = []
    for battle_player in battle_players:
        player_id = battle_player.player_id
        result = results[player_id]
        reward = rewards[player_id]

        player_updates.append({
            'id': battle_player.id,
            'score': result['score'],
            'distance': result['distance'],
            'rank': result['rank'],
            'xp_earned': reward['xp_earned'],
            'lumens_earned': reward['lumens_earned'],
            'capsule_reward_id': reward['capsule_reward_id']
        })

    await battle_repo.update_battle_players_results(db, player_updates)

    # Применить награды
    for battle_player in battle_players:
        player_id = battle_player.player_id
        spirit_id = battle_player.player_spirit_id
        result = results[player_id]

        await rewards_service.apply_battle_rewards(
            player_id=player_id,
            spirit_id=spirit_id,
            rank=result['rank'],
            seed=seed,
            battle_session_id=battle_session.id
        )

    # Завершить battle session
    await battle_repo.finish_battle_session(db, battle_session.id, replay_data)

    await db.commit()

    return {
        "ok": True,
        "data": {
            "battle_session_id": battle_session.id,
            "results": results,
            "rewards": rewards,
            "replay_data": replay_data
        },
        "error": None
    }


@router.get("/battles/history", response_model=dict)
async def get_battle_history(
    limit: int = 20,
    offset: int = 0,
    mode: Optional[str] = None,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить историю боев игрока
    """
    sessions, total = await battle_repo.get_battle_sessions_by_player(
        db,
        player_id=current_user_id,
        mode=mode,
        limit=limit,
        offset=offset
    )

    # Преобразовать в BattleHistoryItem
    items = []
    for session in sessions:
        # Найти запись игрока в battle_players
        player_record = None
        for player in session.players:
            if player.player_id == current_user_id:
                player_record = player
                break

        if player_record:
            items.append({
                'id': session.id,
                'mode': session.mode,
                'started_at': session.started_at,
                'finished_at': session.finished_at,
                'rank': player_record.rank,
                'score': player_record.score,
                'distance': player_record.distance,
                'xp_earned': player_record.xp_earned,
                'lumens_earned': player_record.lumens_earned
            })

    return {
        "ok": True,
        "data": {
            "total": total,
            "items": items
        },
        "error": None
    }


@router.get("/battles/{battle_id}", response_model=dict)
async def get_battle_details(
    battle_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить детали боя
    """
    battle_session = await battle_repo.get_battle_session(db, battle_id)

    if not battle_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle not found"
        )

    # Проверить, что игрок был участником
    is_participant = any(
        player.player_id == current_user_id
        for player in battle_session.players
    )

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You were not a participant in this battle"
        )

    return {
        "ok": True,
        "data": BattleFullResponse.from_orm(battle_session),
        "error": None
    }


@router.get("/battles/{battle_id}/replay", response_model=dict)
async def get_battle_replay(
    battle_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить replay данные боя для визуализации
    """
    battle_session = await battle_repo.get_battle_session(db, battle_id)

    if not battle_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle not found"
        )

    # Проверить, что игрок был участником
    is_participant = any(
        player.player_id == current_user_id
        for player in battle_session.players
    )

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You were not a participant in this battle"
        )

    return {
        "ok": True,
        "data": {
            "battle_id": battle_session.id,
            "mode": battle_session.mode,
            "replay_data": battle_session.result_json
        },
        "error": None
    }
