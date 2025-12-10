"""
Leaderboards система с использованием Redis

Использует Redis Sorted Sets для эффективного хранения и запроса рейтингов
"""
from typing import List, Dict, Optional
from redis import Redis
from datetime import datetime, timedelta


class LeaderboardService:
    """
    Сервис для управления таблицами лидеров

    Использует Redis Sorted Sets для хранения:
    - Global leaderboard (все время)
    - Weekly leaderboard (текущая неделя)
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.global_key = "leaderboard:global:wins"
        self.weekly_key_prefix = "leaderboard:weekly:wins"

    def _get_weekly_key(self) -> str:
        """Получить ключ для недельного leaderboard"""
        # Текущая неделя (ISO week)
        now = datetime.utcnow()
        year, week, _ = now.isocalendar()
        return f"{self.weekly_key_prefix}:{year}:W{week}"

    def add_win(self, player_id: int) -> None:
        """
        Добавить победу игроку

        Обновляет как глобальный, так и недельный leaderboard
        """
        # Увеличить счетчик в глобальном leaderboard
        self.redis.zincrby(self.global_key, 1, str(player_id))

        # Увеличить счетчик в недельном leaderboard
        weekly_key = self._get_weekly_key()
        self.redis.zincrby(weekly_key, 1, str(player_id))

        # Установить TTL для недельного leaderboard (8 дней)
        self.redis.expire(weekly_key, 8 * 24 * 60 * 60)

    def add_battle_participation(self, player_id: int) -> None:
        """
        Добавить участие в бою (для расчета win rate)
        """
        battles_key = "leaderboard:global:battles"
        self.redis.zincrby(battles_key, 1, str(player_id))

        weekly_battles_key = f"leaderboard:weekly:battles:{self._get_weekly_key().split(':')[-2]}:{self._get_weekly_key().split(':')[-1]}"
        self.redis.zincrby(weekly_battles_key, 1, str(player_id))
        self.redis.expire(weekly_battles_key, 8 * 24 * 60 * 60)

    def get_global_top(self, limit: int = 100) -> List[Dict[str, any]]:
        """
        Получить топ игроков в глобальном leaderboard

        Returns:
            Список словарей с rank, player_id, wins
        """
        # Получить топ N игроков (по убыванию wins)
        top_players = self.redis.zrevrange(
            self.global_key,
            0,
            limit - 1,
            withscores=True
        )

        # Получить количество боев для каждого игрока
        battles_key = "leaderboard:global:battles"

        results = []
        for rank, (player_id_bytes, wins) in enumerate(top_players, 1):
            player_id = int(player_id_bytes.decode('utf-8'))

            # Получить количество боев
            battles = self.redis.zscore(battles_key, str(player_id)) or 0

            win_rate = wins / battles if battles > 0 else 0.0

            results.append({
                'rank': rank,
                'player_id': player_id,
                'wins': int(wins),
                'battles_count': int(battles),
                'win_rate': win_rate
            })

        return results

    def get_weekly_top(self, limit: int = 100) -> List[Dict[str, any]]:
        """
        Получить топ игроков в недельном leaderboard

        Returns:
            Список словарей с rank, player_id, wins
        """
        weekly_key = self._get_weekly_key()

        # Получить топ N игроков (по убыванию wins)
        top_players = self.redis.zrevrange(
            weekly_key,
            0,
            limit - 1,
            withscores=True
        )

        # Получить количество боев для каждого игрока
        year_week = f"{weekly_key.split(':')[-2]}:{weekly_key.split(':')[-1]}"
        weekly_battles_key = f"leaderboard:weekly:battles:{year_week}"

        results = []
        for rank, (player_id_bytes, wins) in enumerate(top_players, 1):
            player_id = int(player_id_bytes.decode('utf-8'))

            # Получить количество боев
            battles = self.redis.zscore(weekly_battles_key, str(player_id)) or 0

            win_rate = wins / battles if battles > 0 else 0.0

            results.append({
                'rank': rank,
                'player_id': player_id,
                'wins': int(wins),
                'battles_count': int(battles),
                'win_rate': win_rate
            })

        return results

    def get_player_rank(
        self, player_id: int, leaderboard_type: str = 'global'
    ) -> Optional[Dict[str, any]]:
        """
        Получить ранг конкретного игрока

        Args:
            player_id: ID игрока
            leaderboard_type: 'global' или 'weekly'

        Returns:
            Словарь с rank, player_id, wins, win_rate или None
        """
        if leaderboard_type == 'global':
            key = self.global_key
            battles_key = "leaderboard:global:battles"
        elif leaderboard_type == 'weekly':
            key = self._get_weekly_key()
            year_week = f"{key.split(':')[-2]}:{key.split(':')[-1]}"
            battles_key = f"leaderboard:weekly:battles:{year_week}"
        else:
            raise ValueError(f"Invalid leaderboard_type: {leaderboard_type}")

        # Получить количество побед
        wins = self.redis.zscore(key, str(player_id))

        if wins is None:
            return None

        # Получить ранг (0-indexed, поэтому +1)
        rank = self.redis.zrevrank(key, str(player_id))

        if rank is None:
            return None

        # Получить количество боев
        battles = self.redis.zscore(battles_key, str(player_id)) or 0

        win_rate = wins / battles if battles > 0 else 0.0

        return {
            'rank': rank + 1,
            'player_id': player_id,
            'wins': int(wins),
            'battles_count': int(battles),
            'win_rate': win_rate
        }

    def get_total_players_count(self, leaderboard_type: str = 'global') -> int:
        """Получить общее количество игроков в leaderboard"""
        if leaderboard_type == 'global':
            key = self.global_key
        elif leaderboard_type == 'weekly':
            key = self._get_weekly_key()
        else:
            raise ValueError(f"Invalid leaderboard_type: {leaderboard_type}")

        return self.redis.zcard(key)

    def reset_weekly_leaderboard(self) -> None:
        """
        Сбросить недельный leaderboard (вызывается в начале новой недели)

        Обычно вызывается Celery задачей
        """
        weekly_key = self._get_weekly_key()
        self.redis.delete(weekly_key)

        year_week = f"{weekly_key.split(':')[-2]}:{weekly_key.split(':')[-1]}"
        weekly_battles_key = f"leaderboard:weekly:battles:{year_week}"
        self.redis.delete(weekly_battles_key)
