"""
Pydantic схемы для боевой системы и матчмейкинга
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# Базовые схемы для BattleSession
class BattleSessionBase(BaseModel):
    """Базовая схема сессии боя"""
    mode: str = Field(..., description="Режим игры: flow_flight, deep_dive, rhythm_path, jump_rush, collecting_frenzy")


class BattleSessionCreate(BattleSessionBase):
    """Схема для создания сессии боя"""
    created_by: int = Field(..., description="Telegram ID игрока-инициатора")
    seed: int = Field(..., description="Seed для детерминированной симуляции")


class BattleSessionUpdate(BaseModel):
    """Схема для обновления сессии боя"""
    finished_at: Optional[datetime] = None
    result_json: Optional[Dict[str, Any]] = None


class BattleSessionResponse(BattleSessionBase):
    """Схема ответа с информацией о сессии боя"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    result_json: Optional[Dict[str, Any]] = None
    created_by: int
    seed: int
    created_at: datetime


# Базовые схемы для BattlePlayer
class BattlePlayerBase(BaseModel):
    """Базовая схема участника боя"""
    battle_session_id: int
    player_id: int = Field(..., description="Telegram ID игрока")
    player_spirit_id: int = Field(..., description="ID спирита")
    stats_snapshot: Dict[str, Any] = Field(..., description="Снапшот статов спирита")


class BattlePlayerCreate(BattlePlayerBase):
    """Схема для создания участника боя"""
    pass


class BattlePlayerUpdate(BaseModel):
    """Схема для обновления результатов участника"""
    score: Optional[int] = None
    distance: Optional[float] = None
    rank: Optional[int] = Field(None, ge=1, le=3, description="Место: 1, 2 или 3")
    xp_earned: Optional[int] = Field(None, ge=0)
    lumens_earned: Optional[int] = Field(None, ge=0)
    capsule_reward_id: Optional[int] = None


class BattlePlayerResponse(BattlePlayerBase):
    """Схема ответа с информацией об участнике боя"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    score: Optional[int] = None
    distance: Optional[float] = None
    rank: Optional[int] = None
    xp_earned: Optional[int] = None
    lumens_earned: Optional[int] = None
    capsule_reward_id: Optional[int] = None
    created_at: datetime


# Схемы для полного ответа о бое
class BattleFullResponse(BattleSessionResponse):
    """Полная информация о бою с участниками"""
    players: List[BattlePlayerResponse] = []


# Схемы для матчмейкинга
class MatchmakingJoinRequest(BaseModel):
    """Запрос на присоединение к матчмейкингу"""
    spirit_id: int = Field(..., description="ID активного спирита для боя")
    mode: str = Field(..., description="Режим игры")


class MatchmakingStatus(BaseModel):
    """Статус матчмейкинга"""
    in_queue: bool = Field(..., description="Находится ли игрок в очереди")
    mode: Optional[str] = None
    spirit_id: Optional[int] = None
    queue_position: Optional[int] = None
    estimated_wait_seconds: Optional[int] = None


class MatchFoundNotification(BaseModel):
    """Уведомление о найденном матче"""
    battle_session_id: int
    mode: str
    opponents: List[int] = Field(..., description="Telegram IDs оппонентов")


# Схемы для истории боев
class BattleHistoryRequest(BaseModel):
    """Запрос истории боев"""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    mode: Optional[str] = None


class BattleHistoryItem(BaseModel):
    """Элемент истории боев"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    mode: str
    started_at: datetime
    finished_at: Optional[datetime]
    rank: Optional[int]
    score: Optional[int]
    distance: Optional[float]
    xp_earned: Optional[int]
    lumens_earned: Optional[int]


class BattleHistoryResponse(BaseModel):
    """Ответ с историей боев"""
    total: int
    items: List[BattleHistoryItem]


# Схемы для начала боя
class BattleStartRequest(BaseModel):
    """Запрос на начало боя (внутренний)"""
    battle_session_id: int
    player_ids: List[int] = Field(..., min_length=3, max_length=3, description="3 игрока")
    spirit_ids: List[int] = Field(..., min_length=3, max_length=3, description="3 спирита")


class BattleResult(BaseModel):
    """Результат боя для одного игрока"""
    player_id: int
    spirit_id: int
    score: int
    distance: float
    rank: int
    xp_earned: int
    lumens_earned: int
    capsule_reward_id: Optional[int] = None


class BattleSimulationResult(BaseModel):
    """Результат симуляции боя"""
    battle_session_id: int
    results: List[BattleResult]
    replay_data: Dict[str, Any] = Field(..., description="Данные для replay")


# Схемы для leaderboards
class LeaderboardEntry(BaseModel):
    """Запись в таблице лидеров"""
    rank: int
    player_id: int
    player_name: Optional[str] = None
    score: int
    battles_count: int
    wins_count: int
    win_rate: float = Field(..., ge=0, le=1)


class LeaderboardResponse(BaseModel):
    """Ответ с таблицей лидеров"""
    leaderboard_type: str = Field(..., description="global или weekly")
    total_players: int
    entries: List[LeaderboardEntry]
    user_entry: Optional[LeaderboardEntry] = None
