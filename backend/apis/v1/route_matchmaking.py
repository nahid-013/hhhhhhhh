"""
API эндпоинты для матчмейкинга
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.db.session import get_db
from backend.schemas.battle import (
    MatchmakingJoinRequest,
    MatchmakingStatus,
)
from backend.db.repository import spirit as spirit_repo
from backend.core.security import get_current_user_id
from backend.core.config import get_redis_client
from backend.services.battle.matchmaking import MatchmakingService
from backend.services.battle.engine import SpiritStats


router = APIRouter()


def get_matchmaking_service() -> MatchmakingService:
    """Dependency для получения matchmaking сервиса"""
    redis_client = get_redis_client()
    return MatchmakingService(redis_client)


async def get_spirit_stats_from_player_spirit(db: AsyncSession, spirit_id: int) -> Optional[SpiritStats]:
    """Получить статы спирита для matchmaking"""
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


@router.post("/matchmaking/join", response_model=dict)
async def join_matchmaking(
    request: MatchmakingJoinRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    matchmaking: MatchmakingService = Depends(get_matchmaking_service),
):
    """
    Присоединиться к очереди матчмейкинга

    Проверяет энергию спирита и добавляет в очередь
    """
    # Получить спирита
    spirit = await spirit_repo.get_player_spirit(db, request.spirit_id)

    if not spirit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spirit not found"
        )

    # Проверить ownership
    if spirit.owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your spirit"
        )

    # Проверить энергию
    if spirit.energy < 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient energy: {spirit.energy}/15"
        )

    # Получить статы спирита
    spirit_stats = await get_spirit_stats_from_player_spirit(db, request.spirit_id)

    if not spirit_stats:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate spirit stats"
        )

    # Рассчитать power score
    power_score = matchmaking.calculate_power_score({
        'base_fly': spirit.base_fly,
        'base_maneuver': spirit.base_maneuver,
        'base_run': spirit.base_run,
        'level': spirit.level,
        'rarity_factor': spirit_stats.rarity_factor
    })

    # Подготовить статы для очереди
    stats_dict = {
        'spirit_id': spirit.id,
        'player_id': current_user_id,
        'base_run': spirit.base_run,
        'base_jump': spirit.base_jump,
        'base_swim': spirit.base_swim,
        'base_dives': spirit.base_dives,
        'base_fly': spirit.base_fly,
        'base_maneuver': spirit.base_maneuver,
        'level': spirit.level,
        'rarity_factor': spirit_stats.rarity_factor
    }

    # Добавить в очередь
    success = matchmaking.join_queue(
        mode=request.mode,
        player_id=current_user_id,
        spirit_id=request.spirit_id,
        power_score=power_score,
        stats=stats_dict
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already in queue"
        )

    return {
        "ok": True,
        "data": {
            "message": "Joined matchmaking queue",
            "mode": request.mode,
            "spirit_id": request.spirit_id,
            "power_score": power_score
        },
        "error": None
    }


@router.post("/matchmaking/leave", response_model=dict)
async def leave_matchmaking(
    mode: str,
    current_user_id: int = Depends(get_current_user_id),
    matchmaking: MatchmakingService = Depends(get_matchmaking_service),
):
    """
    Покинуть очередь матчмейкинга
    """
    success = matchmaking.leave_queue(mode, current_user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not in queue"
        )

    return {
        "ok": True,
        "data": {
            "message": "Left matchmaking queue",
            "mode": mode
        },
        "error": None
    }


@router.get("/matchmaking/status", response_model=dict)
async def get_matchmaking_status(
    mode: str,
    current_user_id: int = Depends(get_current_user_id),
    matchmaking: MatchmakingService = Depends(get_matchmaking_service),
):
    """
    Получить статус игрока в очереди матчмейкинга
    """
    status_data = matchmaking.get_status(mode, current_user_id)

    if status_data is None:
        return {
            "ok": True,
            "data": {
                "in_queue": False,
                "mode": mode
            },
            "error": None
        }

    return {
        "ok": True,
        "data": status_data,
        "error": None
    }
