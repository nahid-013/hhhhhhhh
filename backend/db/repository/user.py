"""
Repository для работы с пользователями
"""
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from backend.db.models.user import User, Wallet, BalanceLog, Withdrawal
from backend.schemas.user import UserCreate, UserUpdate
from backend.core.config import settings


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Создание нового пользователя
    """
    user = User(
        tg_id=user_data.tg_id,
        user_name=user_data.user_name,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        language=user_data.language,
        referral_code=user_data.referral_code,
        referraled_by=user_data.referraled_by,
        lumens_balance=Decimal(settings.INITIAL_LUMENS_BALANCE),
        ton_balance=Decimal(settings.INITIAL_TON_BALANCE),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Если есть реферер, увеличиваем его счетчик рефералов
    if user_data.referraled_by:
        await increment_referral_count(db, user_data.referraled_by)
        # Даем бонус рефереру
        await add_balance(
            db,
            user_data.referraled_by,
            Decimal(settings.REFERRAL_BONUS_LUMENS),
            "LUMENS",
            "referral_bonus"
        )

    return user


async def get_user_by_tg_id(db: AsyncSession, tg_id: int) -> Optional[User]:
    """
    Получение пользователя по Telegram ID
    """
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    return result.scalars().first()


async def get_user_by_referral_code(db: AsyncSession, code: str) -> Optional[User]:
    """
    Получение пользователя по реферальному коду
    """
    result = await db.execute(select(User).where(User.referral_code == code))
    return result.scalars().first()


async def update_user(db: AsyncSession, tg_id: int, user_data: UserUpdate) -> Optional[User]:
    """
    Обновление данных пользователя
    """
    stmt = (
        update(User)
        .where(User.tg_id == tg_id)
        .values(**user_data.dict(exclude_unset=True))
        .returning(User)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalars().first()


async def increment_referral_count(db: AsyncSession, tg_id: int) -> None:
    """
    Увеличение счетчика рефералов
    """
    await db.execute(
        update(User)
        .where(User.tg_id == tg_id)
        .values(referrals_count=User.referrals_count + 1)
    )
    await db.commit()


async def get_referrals(db: AsyncSession, tg_id: int) -> List[User]:
    """
    Получение списка рефералов пользователя
    """
    result = await db.execute(
        select(User).where(User.referraled_by == tg_id).order_by(User.created_at.desc())
    )
    return result.scalars().all()


async def add_balance(
    db: AsyncSession,
    tg_id: int,
    amount: Decimal,
    currency: str,
    reason: str
) -> None:
    """
    Добавление баланса пользователю с логированием
    """
    async with db.begin_nested():
        # Блокируем пользователя для обновления
        result = await db.execute(
            select(User).where(User.tg_id == tg_id).with_for_update()
        )
        user = result.scalars().first()
        if not user:
            raise ValueError(f"User {tg_id} not found")

        # Обновляем баланс
        if currency.upper() == "TON":
            user.ton_balance += amount
        elif currency.upper() == "LUMENS":
            user.lumens_balance += amount
        else:
            raise ValueError(f"Unknown currency: {currency}")

        # Создаем лог
        log = BalanceLog(
            tg_id=tg_id,
            change=amount,
            currency=currency.upper(),
            reason=reason
        )
        db.add(log)

    await db.commit()


async def subtract_balance(
    db: AsyncSession,
    tg_id: int,
    amount: Decimal,
    currency: str,
    reason: str
) -> None:
    """
    Списание баланса пользователя с логированием
    """
    async with db.begin_nested():
        # Блокируем пользователя для обновления
        result = await db.execute(
            select(User).where(User.tg_id == tg_id).with_for_update()
        )
        user = result.scalars().first()
        if not user:
            raise ValueError(f"User {tg_id} not found")

        # Проверяем достаточность средств
        if currency.upper() == "TON":
            if user.ton_balance < amount:
                raise ValueError("Insufficient TON balance")
            user.ton_balance -= amount
        elif currency.upper() == "LUMENS":
            if user.lumens_balance < amount:
                raise ValueError("Insufficient Lumens balance")
            user.lumens_balance -= amount
        else:
            raise ValueError(f"Unknown currency: {currency}")

        # Создаем лог
        log = BalanceLog(
            tg_id=tg_id,
            change=-amount,
            currency=currency.upper(),
            reason=reason
        )
        db.add(log)

    await db.commit()


async def connect_wallet(db: AsyncSession, tg_id: int, address: str) -> Wallet:
    """
    Подключение TON кошелька к профилю
    """
    # Проверяем, не подключен ли уже этот кошелек
    result = await db.execute(select(Wallet).where(Wallet.address == address))
    existing_wallet = result.scalars().first()
    if existing_wallet:
        raise ValueError("Wallet already connected to another account")

    # Обновляем адрес в профиле пользователя
    await db.execute(
        update(User)
        .where(User.tg_id == tg_id)
        .values(ton_address=address)
    )

    # Создаем запись о кошельке
    wallet = Wallet(tg_id=tg_id, address=address)
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


async def create_withdrawal(
    db: AsyncSession,
    tg_id: int,
    amount: Decimal,
    currency: str
) -> Withdrawal:
    """
    Создание запроса на вывод средств
    """
    # Списываем баланс
    await subtract_balance(db, tg_id, amount, currency, "withdrawal_request")

    # Создаем запись о выводе
    withdrawal = Withdrawal(
        tg_id=tg_id,
        amount=amount,
        currency=currency.upper(),
        status="pending"
    )
    db.add(withdrawal)
    await db.commit()
    await db.refresh(withdrawal)
    return withdrawal


async def get_user_withdrawals(db: AsyncSession, tg_id: int) -> List[Withdrawal]:
    """
    Получение истории выводов пользователя
    """
    result = await db.execute(
        select(Withdrawal)
        .where(Withdrawal.tg_id == tg_id)
        .order_by(Withdrawal.created_at.desc())
    )
    return result.scalars().all()
