"""
Matchmaking система с использованием Redis

Реализует skill-based matching с расширяющимся tolerance по мере ожидания
"""
import json
import time
from typing import List, Optional, Dict, Any
from redis import Redis
from backend.services.battle.engine import SpiritStats


class MatchmakingQueue:
    """
    Очередь матчмейкинга для определенного режима игры

    Использует Redis для хранения игроков в очереди
    """

    def __init__(self, redis_client: Redis, mode: str):
        self.redis = redis_client
        self.mode = mode
        self.queue_key = f"matchmaking:queue:{mode}"
        self.player_data_key = f"matchmaking:player_data:{mode}"

    def add_player(
        self,
        player_id: int,
        spirit_id: int,
        power_score: float,
        stats: Dict[str, Any]
    ) -> bool:
        """
        Добавить игрока в очередь

        Args:
            player_id: Telegram ID игрока
            spirit_id: ID активного спирита
            power_score: Сила спирита для matching
            stats: Полные статы спирита

        Returns:
            True если успешно добавлен, False если уже в очереди
        """
        # Проверить, не в очереди ли уже игрок
        if self.is_player_in_queue(player_id):
            return False

        # Сохранить данные игрока
        player_data = {
            'player_id': player_id,
            'spirit_id': spirit_id,
            'power_score': power_score,
            'stats': stats,
            'joined_at': time.time()
        }

        # Добавить в sorted set по power_score для skill-based matching
        self.redis.zadd(self.queue_key, {str(player_id): power_score})

        # Сохранить полные данные
        self.redis.hset(
            self.player_data_key,
            str(player_id),
            json.dumps(player_data)
        )

        return True

    def remove_player(self, player_id: int) -> bool:
        """
        Удалить игрока из очереди

        Returns:
            True если успешно удален
        """
        # Удалить из sorted set
        removed_count = self.redis.zrem(self.queue_key, str(player_id))

        # Удалить данные
        self.redis.hdel(self.player_data_key, str(player_id))

        return removed_count > 0

    def is_player_in_queue(self, player_id: int) -> bool:
        """Проверить, находится ли игрок в очереди"""
        return self.redis.zscore(self.queue_key, str(player_id)) is not None

    def get_player_data(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные игрока из очереди"""
        data = self.redis.hget(self.player_data_key, str(player_id))
        if data:
            return json.loads(data)
        return None

    def get_queue_size(self) -> int:
        """Получить размер очереди"""
        return self.redis.zcard(self.queue_key)

    def find_match(self) -> Optional[List[Dict[str, Any]]]:
        """
        Найти матч для 3 игроков

        Использует skill-based matching с учетом времени ожидания

        Returns:
            Список из 3 игроков если матч найден, иначе None
        """
        queue_size = self.get_queue_size()

        if queue_size < 3:
            return None

        # Получить всех игроков в очереди
        all_players = self.redis.zrange(self.queue_key, 0, -1, withscores=True)

        # Конвертировать в список с данными
        players_list = []
        current_time = time.time()

        for player_id_bytes, power_score in all_players:
            player_id = int(player_id_bytes.decode('utf-8'))
            player_data = self.get_player_data(player_id)

            if player_data:
                # Рассчитать время ожидания
                wait_time = current_time - player_data['joined_at']

                # Tolerance расширяется: +10% каждые 10 секунд ожидания
                tolerance_multiplier = 1.0 + (wait_time / 10.0) * 0.1

                player_data['wait_time'] = wait_time
                player_data['tolerance_multiplier'] = tolerance_multiplier
                players_list.append(player_data)

        # Попробовать найти матч для каждого игрока
        for i, base_player in enumerate(players_list):
            base_power = base_player['power_score']
            tolerance = base_power * base_player['tolerance_multiplier'] * 0.2

            # Найти подходящих оппонентов
            matched_players = [base_player]

            for j, other_player in enumerate(players_list):
                if i == j:
                    continue

                other_power = other_player['power_score']

                # Проверить, подходит ли по силе
                if abs(base_power - other_power) <= tolerance:
                    matched_players.append(other_player)

                    if len(matched_players) == 3:
                        # Матч найден! Удалить игроков из очереди
                        for player in matched_players:
                            self.remove_player(player['player_id'])

                        return matched_players

        # Матч не найден
        return None


class MatchmakingService:
    """Главный сервис матчмейкинга"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.queues: Dict[str, MatchmakingQueue] = {}

    def get_queue(self, mode: str) -> MatchmakingQueue:
        """Получить или создать очередь для режима"""
        if mode not in self.queues:
            self.queues[mode] = MatchmakingQueue(self.redis, mode)
        return self.queues[mode]

    def join_queue(
        self,
        mode: str,
        player_id: int,
        spirit_id: int,
        power_score: float,
        stats: Dict[str, Any]
    ) -> bool:
        """Присоединиться к очереди"""
        queue = self.get_queue(mode)
        return queue.add_player(player_id, spirit_id, power_score, stats)

    def leave_queue(self, mode: str, player_id: int) -> bool:
        """Покинуть очередь"""
        queue = self.get_queue(mode)
        return queue.remove_player(player_id)

    def leave_all_queues(self, player_id: int) -> None:
        """Покинуть все очереди (на всякий случай)"""
        modes = ['flow_flight', 'deep_dive', 'rhythm_path', 'jump_rush', 'collecting_frenzy']
        for mode in modes:
            queue = self.get_queue(mode)
            queue.remove_player(player_id)

    def get_status(self, mode: str, player_id: int) -> Optional[Dict[str, Any]]:
        """Получить статус игрока в очереди"""
        queue = self.get_queue(mode)

        if not queue.is_player_in_queue(player_id):
            return None

        player_data = queue.get_player_data(player_id)
        queue_size = queue.get_queue_size()

        # Примерная позиция в очереди (по power_score)
        rank = self.redis.zrank(queue.queue_key, str(player_id))

        return {
            'in_queue': True,
            'mode': mode,
            'spirit_id': player_data['spirit_id'],
            'queue_size': queue_size,
            'queue_position': rank + 1 if rank is not None else None,
            'wait_time': time.time() - player_data['joined_at'],
            'estimated_wait_seconds': self._estimate_wait_time(queue_size)
        }

    def find_matches(self, mode: str) -> List[List[Dict[str, Any]]]:
        """
        Найти все возможные матчи в очереди

        Returns:
            Список матчей (каждый матч - список из 3 игроков)
        """
        queue = self.get_queue(mode)
        matches = []

        while True:
            match = queue.find_match()
            if match is None:
                break
            matches.append(match)

        return matches

    def _estimate_wait_time(self, queue_size: int) -> int:
        """
        Оценить время ожидания на основе размера очереди

        Это примерная оценка. В реальности зависит от частоты входа игроков.
        """
        if queue_size >= 3:
            return 5  # Матч скоро будет найден
        elif queue_size == 2:
            return 20  # Ждем еще одного игрока
        else:
            return 60  # Ждем двух игроков

    def calculate_power_score(self, stats_dict: Dict[str, Any]) -> float:
        """
        Рассчитать power score из словаря статов

        Для Flow Flight: (fly * 2.0 + maneuver * 1.5 + base_run * 1.0 + level * 5) * rarity_factor
        """
        power = (
            stats_dict.get('base_fly', 1) * 2.0 +
            stats_dict.get('base_maneuver', 1) * 1.5 +
            stats_dict.get('base_run', 1) * 1.0 +
            stats_dict.get('level', 1) * 5
        ) * stats_dict.get('rarity_factor', 1.0)

        return power
