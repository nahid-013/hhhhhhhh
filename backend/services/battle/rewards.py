"""
Система наград за бои

Управляет начислением XP, Lumens и капсул после боя
"""
import random
from typing import Dict, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.user import User, BalanceLog
from backend.db.models.spirit import PlayerSpirit
from backend.db.models.capsule import PlayerCapsule, CapsuleTemplate


# Таблица наград по рангам
REWARDS_TABLE = {
    1: {
        'xp': 100,
        'lumens': 150,
        'capsule_chance': 0.05,  # 5% шанс
    },
    2: {
        'xp': 70,
        'lumens': 100,
        'capsule_chance': 0.03,  # 3% шанс
    },
    3: {
        'xp': 50,
        'lumens': 70,
        'capsule_chance': 0.01,  # 1% шанс
    }
}

# XP для следующего уровня: floor(100 * level^1.2)
def calculate_xp_for_next_level(level: int) -> int:
    """Рассчитать XP для следующего уровня"""
    return int(100 * (level ** 1.2))


class RewardsService:
    """Сервис начисления наград"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply_battle_rewards(
        self,
        player_id: int,
        spirit_id: int,
        rank: int,
        seed: int,
        battle_session_id: int
    ) -> Dict[str, any]:
        """
        Применить награды после боя

        Args:
            player_id: Telegram ID игрока
            spirit_id: ID спирита
            rank: Место в бою (1, 2, 3)
            seed: Seed для детерминированности наград
            battle_session_id: ID сессии боя

        Returns:
            Словарь с примененными наградами
        """
        if rank not in REWARDS_TABLE:
            raise ValueError(f"Invalid rank: {rank}")

        rewards = REWARDS_TABLE[rank]

        # 1. Начислить XP спириту и проверить level up
        spirit_result = await self._apply_spirit_xp(
            spirit_id, rewards['xp']
        )

        # 2. Начислить Lumens игроку
        await self._apply_lumens(
            player_id, rewards['lumens'], battle_session_id
        )

        # 3. Проверить выпадение капсулы
        capsule_id = await self._try_drop_capsule(
            player_id, rewards['capsule_chance'], seed
        )

        return {
            'xp_earned': rewards['xp'],
            'lumens_earned': rewards['lumens'],
            'capsule_reward_id': capsule_id,
            'spirit_leveled_up': spirit_result['leveled_up'],
            'spirit_new_level': spirit_result['new_level']
        }

    async def _apply_spirit_xp(
        self, spirit_id: int, xp_amount: int
    ) -> Dict[str, any]:
        """
        Начислить XP спириту и обработать level up

        Returns:
            {'leveled_up': bool, 'new_level': int}
        """
        # Получить спирита
        result = await self.db.execute(
            select(PlayerSpirit)
            .where(PlayerSpirit.id == spirit_id)
            .with_for_update()
        )
        spirit = result.scalar_one_or_none()

        if not spirit:
            raise ValueError(f"Spirit {spirit_id} not found")

        # Начислить XP
        spirit.xp += xp_amount

        leveled_up = False
        original_level = spirit.level

        # Проверить level up
        while True:
            xp_needed = calculate_xp_for_next_level(spirit.level)

            if spirit.xp >= xp_needed:
                # Level up!
                spirit.level += 1
                spirit.xp -= xp_needed
                leveled_up = True
            else:
                break

        await self.db.flush()

        return {
            'leveled_up': leveled_up,
            'new_level': spirit.level,
            'levels_gained': spirit.level - original_level
        }

    async def _apply_lumens(
        self, player_id: int, lumens_amount: int, battle_session_id: int
    ) -> None:
        """Начислить Lumens игроку"""
        # Получить пользователя
        result = await self.db.execute(
            select(User)
            .where(User.tg_id == player_id)
            .with_for_update()
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {player_id} not found")

        # Начислить Lumens
        user.lumens_balance += lumens_amount

        # Создать лог баланса
        balance_log = BalanceLog(
            tg_id=player_id,
            change=lumens_amount,
            currency='lumens',
            reason=f'battle_reward_session_{battle_session_id}'
        )
        self.db.add(balance_log)

        await self.db.flush()

    async def _try_drop_capsule(
        self, player_id: int, drop_chance: float, seed: int
    ) -> Optional[int]:
        """
        Попытаться выдать капсулу с определенным шансом

        Returns:
            ID капсулы если выпала, иначе None
        """
        # Детерминированная проверка шанса
        rng = random.Random(seed + player_id)

        if rng.random() > drop_chance:
            return None

        # Получить доступные капсулы (common rarity для наград)
        result = await self.db.execute(
            select(CapsuleTemplate)
            .where(CapsuleTemplate.is_available == True)
            .where(CapsuleTemplate.rarity_id == 1)  # Common
            .limit(10)
        )
        capsule_templates = list(result.scalars().all())

        if not capsule_templates:
            # Нет доступных капсул
            return None

        # Выбрать случайную капсулу
        capsule_template = rng.choice(capsule_templates)

        # Выдать капсулу игроку
        # Проверить, есть ли уже такая капсула у игрока
        result = await self.db.execute(
            select(PlayerCapsule)
            .where(PlayerCapsule.owner_id == player_id)
            .where(PlayerCapsule.capsule_template_id == capsule_template.id)
            .with_for_update()
        )
        player_capsule = result.scalar_one_or_none()

        if player_capsule:
            # Увеличить quantity
            player_capsule.quantity += 1
        else:
            # Создать новую капсулу
            player_capsule = PlayerCapsule(
                owner_id=player_id,
                capsule_template_id=capsule_template.id,
                quantity=1
            )
            self.db.add(player_capsule)

        await self.db.flush()

        return capsule_template.id

    async def deduct_energy(self, spirit_id: int, amount: int = 15) -> None:
        """
        Списать энергию у спирита

        Args:
            spirit_id: ID спирита
            amount: Количество энергии (по умолчанию 15)
        """
        result = await self.db.execute(
            select(PlayerSpirit)
            .where(PlayerSpirit.id == spirit_id)
            .with_for_update()
        )
        spirit = result.scalar_one_or_none()

        if not spirit:
            raise ValueError(f"Spirit {spirit_id} not found")

        if spirit.energy < amount:
            raise ValueError(f"Insufficient energy: {spirit.energy} < {amount}")

        spirit.energy -= amount
        await self.db.flush()

    async def check_energy_sufficient(
        self, spirit_id: int, required: int = 15
    ) -> bool:
        """Проверить, достаточно ли энергии у спирита"""
        result = await self.db.execute(
            select(PlayerSpirit.energy)
            .where(PlayerSpirit.id == spirit_id)
        )
        energy = result.scalar_one_or_none()

        if energy is None:
            return False

        return energy >= required
