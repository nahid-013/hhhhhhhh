"""
API эндпоинты для таблиц лидеров
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.db.session import get_db
from backend.schemas.battle import LeaderboardResponse, LeaderboardEntry
from backend.core.security import get_current_user_id
from backend.core.config import get_redis_client
from backend.services.battle.leaderboards import LeaderboardService
from backend.db.repository import user as user_repo


router = APIRouter()


def get_leaderboard_service() -> LeaderboardService:
    """Dependency для получения leaderboard сервиса"""
    redis_client = get_redis_client()
    return LeaderboardService(redis_client)


@router.get("/leaderboards/global", response_model=dict)
async def get_global_leaderboard(
    limit: int = 100,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    leaderboards: LeaderboardService = Depends(get_leaderboard_service),
):
    """
    Получить глобальный leaderboard

    Возвращает топ игроков по всему времени + позицию текущего пользователя
    """
    # Получить топ игроков
    top_entries = leaderboards.get_global_top(limit=limit)

    # Получить имена игроков
    entries_with_names = []
    for entry in top_entries:
        user = await user_repo.get_user(db, entry['player_id'])
        player_name = user.user_name if user and user.user_name else f"Player_{entry['player_id']}"

        entries_with_names.append(LeaderboardEntry(
            rank=entry['rank'],
            player_id=entry['player_id'],
            player_name=player_name,
            score=entry['wins'],  # Score = wins
            battles_count=entry['battles_count'],
            wins_count=entry['wins'],
            win_rate=entry['win_rate']
        ))

    # Получить позицию текущего пользователя
    user_entry_data = leaderboards.get_player_rank(current_user_id, 'global')

    user_entry = None
    if user_entry_data:
        user = await user_repo.get_user(db, current_user_id)
        player_name = user.user_name if user and user.user_name else f"Player_{current_user_id}"

        user_entry = LeaderboardEntry(
            rank=user_entry_data['rank'],
            player_id=current_user_id,
            player_name=player_name,
            score=user_entry_data['wins'],
            battles_count=user_entry_data['battles_count'],
            wins_count=user_entry_data['wins'],
            win_rate=user_entry_data['win_rate']
        )

    total_players = leaderboards.get_total_players_count('global')

    response = LeaderboardResponse(
        leaderboard_type='global',
        total_players=total_players,
        entries=entries_with_names,
        user_entry=user_entry
    )

    return {
        "ok": True,
        "data": response,
        "error": None
    }


@router.get("/leaderboards/weekly", response_model=dict)
async def get_weekly_leaderboard(
    limit: int = 100,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    leaderboards: LeaderboardService = Depends(get_leaderboard_service),
):
    """
    Получить недельный leaderboard

    Возвращает топ игроков за текущую неделю + позицию текущего пользователя
    """
    # Получить топ игроков
    top_entries = leaderboards.get_weekly_top(limit=limit)

    # Получить имена игроков
    entries_with_names = []
    for entry in top_entries:
        user = await user_repo.get_user(db, entry['player_id'])
        player_name = user.user_name if user and user.user_name else f"Player_{entry['player_id']}"

        entries_with_names.append(LeaderboardEntry(
            rank=entry['rank'],
            player_id=entry['player_id'],
            player_name=player_name,
            score=entry['wins'],  # Score = wins
            battles_count=entry['battles_count'],
            wins_count=entry['wins'],
            win_rate=entry['win_rate']
        ))

    # Получить позицию текущего пользователя
    user_entry_data = leaderboards.get_player_rank(current_user_id, 'weekly')

    user_entry = None
    if user_entry_data:
        user = await user_repo.get_user(db, current_user_id)
        player_name = user.user_name if user and user.user_name else f"Player_{current_user_id}"

        user_entry = LeaderboardEntry(
            rank=user_entry_data['rank'],
            player_id=current_user_id,
            player_name=player_name,
            score=user_entry_data['wins'],
            battles_count=user_entry_data['battles_count'],
            wins_count=user_entry_data['wins'],
            win_rate=user_entry_data['win_rate']
        )

    total_players = leaderboards.get_total_players_count('weekly')

    response = LeaderboardResponse(
        leaderboard_type='weekly',
        total_players=total_players,
        entries=entries_with_names,
        user_entry=user_entry
    )

    return {
        "ok": True,
        "data": response,
        "error": None
    }
