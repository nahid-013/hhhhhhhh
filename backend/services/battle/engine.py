"""
Battle Engine для детерминированной симуляции боев

Реализует игровую механику Flow Flight - гонку с препятствиями в воздухе
"""
import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class SpiritStats:
    """Характеристики спирита для боя"""
    spirit_id: int
    player_id: int
    base_run: int
    base_jump: int
    base_swim: int
    base_dives: int
    base_fly: int
    base_maneuver: int
    level: int
    rarity_factor: float  # 1.0 для common, 1.2 для rare, 1.5 для epic, 2.0 для legendary


@dataclass
class ObstacleType:
    """Тип препятствия"""
    name: str
    difficulty: float
    required_stat: str  # 'fly', 'maneuver', 'base_run'


# Константы симуляции
SIMULATION_DURATION = 60.0  # секунд
TICK_RATE = 0.1  # тик каждые 0.1 секунды
BASE_SPEED = 10.0  # базовая скорость движения
OBSTACLE_SPAWN_CHANCE = 0.15  # 15% шанс появления препятствия на каждом тике

# Типы препятствий для Flow Flight
OBSTACLES = [
    ObstacleType(name="wind_gust", difficulty=1.0, required_stat="maneuver"),
    ObstacleType(name="narrow_gap", difficulty=1.2, required_stat="maneuver"),
    ObstacleType(name="updraft", difficulty=0.8, required_stat="fly"),
    ObstacleType(name="downdraft", difficulty=1.5, required_stat="fly"),
    ObstacleType(name="cloud_wall", difficulty=1.3, required_stat="base_run"),
]


class FlowFlightEngine:
    """
    Движок для симуляции Flow Flight

    Flow Flight - это гонка в воздухе, где игроки должны пролететь максимальное расстояние,
    избегая препятствия. Ключевые статы: fly, maneuver, base_run
    """

    def __init__(self, seed: int):
        """Инициализация с детерминированным seed"""
        self.seed = seed
        self.rng = random.Random(seed)

    def calculate_power_score(self, stats: SpiritStats) -> float:
        """
        Рассчитать силу спирита для Flow Flight

        Формула: (fly * 2.0 + maneuver * 1.5 + base_run * 1.0 + level * 5) * rarity_factor
        """
        power = (
            stats.base_fly * 2.0 +
            stats.base_maneuver * 1.5 +
            stats.base_run * 1.0 +
            stats.level * 5
        ) * stats.rarity_factor

        return power

    def handle_obstacle(
        self, stats: SpiritStats, obstacle: ObstacleType
    ) -> Tuple[bool, float]:
        """
        Обработать препятствие

        Returns:
            (success, speed_multiplier) - успешно ли преодолено и множитель скорости
        """
        # Получить нужный стат для препятствия
        stat_value = getattr(stats, obstacle.required_stat)

        # Шанс успеха зависит от стата и сложности
        success_chance = min(0.95, stat_value / (obstacle.difficulty * 20))

        # Детерминированная проверка успеха
        success = self.rng.random() < success_chance

        if success:
            # При успехе - небольшой бонус к скорости
            speed_mult = 1.0 + (stat_value / 100.0)
        else:
            # При неудаче - замедление
            speed_mult = 0.5 - (obstacle.difficulty * 0.1)

        return success, max(0.1, speed_mult)

    def simulate(self, spirits: List[SpiritStats]) -> Dict[int, Any]:
        """
        Запустить симуляцию боя

        Args:
            spirits: Список спиритов (должно быть ровно 3)

        Returns:
            Результаты симуляции для каждого игрока
        """
        if len(spirits) != 3:
            raise ValueError("Flow Flight требует ровно 3 участников")

        # Инициализация состояния каждого игрока
        player_states = {
            spirit.player_id: {
                'spirit_id': spirit.spirit_id,
                'distance': 0.0,
                'current_speed': BASE_SPEED,
                'power_score': self.calculate_power_score(spirit),
                'obstacles_hit': 0,
                'obstacles_avoided': 0,
                'events': []  # Лог событий для replay
            }
            for spirit in spirits
        }

        # Создать lookup по player_id
        spirits_lookup = {spirit.player_id: spirit for spirit in spirits}

        # Симуляция по тикам
        current_time = 0.0
        while current_time < SIMULATION_DURATION:
            for spirit in spirits:
                player_id = spirit.player_id
                state = player_states[player_id]

                # Проверка появления препятствия
                if self.rng.random() < OBSTACLE_SPAWN_CHANCE:
                    obstacle = self.rng.choice(OBSTACLES)

                    success, speed_mult = self.handle_obstacle(spirit, obstacle)

                    if success:
                        state['obstacles_avoided'] += 1
                        state['events'].append({
                            'time': current_time,
                            'type': 'obstacle_avoided',
                            'obstacle': obstacle.name,
                            'speed_mult': speed_mult
                        })
                    else:
                        state['obstacles_hit'] += 1
                        state['events'].append({
                            'time': current_time,
                            'type': 'obstacle_hit',
                            'obstacle': obstacle.name,
                            'speed_mult': speed_mult
                        })

                    # Обновить скорость
                    state['current_speed'] = BASE_SPEED * speed_mult

                # Двигаться вперед
                distance_increment = state['current_speed'] * TICK_RATE

                # Добавить случайную вариацию (детерминированную)
                variation = self.rng.uniform(-0.5, 0.5)
                distance_increment += variation

                state['distance'] += max(0, distance_increment)

                # Скорость постепенно возвращается к норме
                state['current_speed'] = (
                    state['current_speed'] * 0.9 + BASE_SPEED * 0.1
                )

            current_time += TICK_RATE

        # Рассчитать финальные результаты
        results = {}
        for player_id, state in player_states.items():
            # Финальный score = distance + бонусы
            bonus = (
                state['obstacles_avoided'] * 5.0 -
                state['obstacles_hit'] * 3.0
            )
            final_score = int(state['distance'] + bonus)

            results[player_id] = {
                'spirit_id': state['spirit_id'],
                'distance': round(state['distance'], 2),
                'score': final_score,
                'power_score': state['power_score'],
                'obstacles_avoided': state['obstacles_avoided'],
                'obstacles_hit': state['obstacles_hit'],
                'events': state['events']  # Для replay
            }

        return results


class BattleSimulator:
    """Главный класс для симуляции боев"""

    def __init__(self, seed: int):
        self.seed = seed

    def simulate_flow_flight(
        self, spirits: List[SpiritStats]
    ) -> Tuple[Dict[int, Any], Dict[str, Any]]:
        """
        Симулировать Flow Flight бой

        Returns:
            (results, replay_data) - результаты и данные для replay
        """
        engine = FlowFlightEngine(self.seed)
        results = engine.simulate(spirits)

        # Определить ранги
        sorted_players = sorted(
            results.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )

        for rank, (player_id, data) in enumerate(sorted_players, 1):
            results[player_id]['rank'] = rank

        # Собрать данные для replay
        replay_data = {
            'mode': 'flow_flight',
            'seed': self.seed,
            'duration': SIMULATION_DURATION,
            'players': results
        }

        return results, replay_data

    def calculate_rewards(
        self, results: Dict[int, Any]
    ) -> Dict[int, Dict[str, int]]:
        """
        Рассчитать награды для каждого игрока

        Rewards based on rank:
        - 1st place: 100 XP, 150 Lumens, 5% шанс капсулы
        - 2nd place: 70 XP, 100 Lumens, 3% шанс капсулы
        - 3rd place: 50 XP, 70 Lumens, 1% шанс капсулы
        """
        rewards_table = {
            1: {'xp': 100, 'lumens': 150, 'capsule_chance': 0.05},
            2: {'xp': 70, 'lumens': 100, 'capsule_chance': 0.03},
            3: {'xp': 50, 'lumens': 70, 'capsule_chance': 0.01},
        }

        rewards = {}
        rng = random.Random(self.seed + 12345)  # Другой seed для наград

        for player_id, data in results.items():
            rank = data['rank']
            rank_rewards = rewards_table[rank]

            # Базовые награды
            player_rewards = {
                'xp_earned': rank_rewards['xp'],
                'lumens_earned': rank_rewards['lumens'],
                'capsule_reward_id': None
            }

            # Шанс получить капсулу
            if rng.random() < rank_rewards['capsule_chance']:
                # TODO: В будущем выбрать случайную капсулу из доступных
                # Пока просто флаг
                player_rewards['capsule_reward_id'] = 1

            rewards[player_id] = player_rewards

        return rewards
