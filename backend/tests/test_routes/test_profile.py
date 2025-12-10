"""
Тесты для profile endpoints
"""
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.repository import user as user_repo
from backend.schemas.user import UserCreate, UserUpdate
from backend.core.security import generate_referral_code


@pytest.mark.asyncio
async def test_update_user(test_db: AsyncSession):
    """Тест обновления профиля пользователя"""
    tg_id = 123456789
    referral_code = generate_referral_code(tg_id)

    # Создаем пользователя
    user_data = UserCreate(
        tg_id=tg_id,
        user_name="testuser",
        first_name="Test",
        last_name="User",
        language="ru",
        referral_code=referral_code,
        referraled_by=None,
    )
    user = await user_repo.create_user(test_db, user_data)

    # Обновляем пользователя
    update_data = UserUpdate(
        first_name="Updated",
        last_name="Name",
    )
    updated_user = await user_repo.update_user(test_db, tg_id, update_data)

    assert updated_user is not None
    assert updated_user.first_name == "Updated"
    assert updated_user.last_name == "Name"
    assert updated_user.user_name == "testuser"  # Не изменилось


@pytest.mark.asyncio
async def test_connect_wallet(test_db: AsyncSession):
    """Тест подключения TON кошелька"""
    tg_id = 123456789
    referral_code = generate_referral_code(tg_id)

    # Создаем пользователя
    user_data = UserCreate(
        tg_id=tg_id,
        user_name="testuser",
        first_name="Test",
        last_name="User",
        language="ru",
        referral_code=referral_code,
        referraled_by=None,
    )
    await user_repo.create_user(test_db, user_data)

    # Подключаем кошелек
    wallet_address = "EQD1234567890abcdef"
    wallet = await user_repo.connect_wallet(test_db, tg_id, wallet_address)

    assert wallet is not None
    assert wallet.address == wallet_address
    assert wallet.tg_id == tg_id

    # Проверяем, что адрес обновился в профиле
    user = await user_repo.get_user_by_tg_id(test_db, tg_id)
    assert user.ton_address == wallet_address


@pytest.mark.asyncio
async def test_add_balance(test_db: AsyncSession):
    """Тест добавления баланса"""
    tg_id = 123456789
    referral_code = generate_referral_code(tg_id)

    # Создаем пользователя
    user_data = UserCreate(
        tg_id=tg_id,
        user_name="testuser",
        first_name="Test",
        last_name="User",
        language="ru",
        referral_code=referral_code,
        referraled_by=None,
    )
    user = await user_repo.create_user(test_db, user_data)
    initial_balance = user.lumens_balance

    # Добавляем баланс
    amount = Decimal("500")
    await user_repo.add_balance(test_db, tg_id, amount, "LUMENS", "test_deposit")

    # Проверяем новый баланс
    updated_user = await user_repo.get_user_by_tg_id(test_db, tg_id)
    assert updated_user.lumens_balance == initial_balance + amount


@pytest.mark.asyncio
async def test_subtract_balance(test_db: AsyncSession):
    """Тест списания баланса"""
    tg_id = 123456789
    referral_code = generate_referral_code(tg_id)

    # Создаем пользователя
    user_data = UserCreate(
        tg_id=tg_id,
        user_name="testuser",
        first_name="Test",
        last_name="User",
        language="ru",
        referral_code=referral_code,
        referraled_by=None,
    )
    user = await user_repo.create_user(test_db, user_data)
    initial_balance = user.lumens_balance

    # Списываем баланс
    amount = Decimal("200")
    await user_repo.subtract_balance(test_db, tg_id, amount, "LUMENS", "test_purchase")

    # Проверяем новый баланс
    updated_user = await user_repo.get_user_by_tg_id(test_db, tg_id)
    assert updated_user.lumens_balance == initial_balance - amount


@pytest.mark.asyncio
async def test_subtract_balance_insufficient_funds(test_db: AsyncSession):
    """Тест списания баланса при недостаточности средств"""
    tg_id = 123456789
    referral_code = generate_referral_code(tg_id)

    # Создаем пользователя
    user_data = UserCreate(
        tg_id=tg_id,
        user_name="testuser",
        first_name="Test",
        last_name="User",
        language="ru",
        referral_code=referral_code,
        referraled_by=None,
    )
    await user_repo.create_user(test_db, user_data)

    # Пытаемся списать больше, чем есть
    amount = Decimal("10000")
    with pytest.raises(ValueError, match="Insufficient Lumens balance"):
        await user_repo.subtract_balance(test_db, tg_id, amount, "LUMENS", "test_purchase")


@pytest.mark.asyncio
async def test_create_withdrawal(test_db: AsyncSession):
    """Тест создания запроса на вывод"""
    tg_id = 123456789
    referral_code = generate_referral_code(tg_id)

    # Создаем пользователя
    user_data = UserCreate(
        tg_id=tg_id,
        user_name="testuser",
        first_name="Test",
        last_name="User",
        language="ru",
        referral_code=referral_code,
        referraled_by=None,
    )
    user = await user_repo.create_user(test_db, user_data)

    # Добавляем TON баланс
    await user_repo.add_balance(test_db, tg_id, Decimal("10"), "TON", "test_deposit")

    # Создаем запрос на вывод
    amount = Decimal("5")
    withdrawal = await user_repo.create_withdrawal(test_db, tg_id, amount, "TON")

    assert withdrawal is not None
    assert withdrawal.amount == amount
    assert withdrawal.currency == "TON"
    assert withdrawal.status == "pending"

    # Проверяем, что баланс уменьшился
    updated_user = await user_repo.get_user_by_tg_id(test_db, tg_id)
    assert updated_user.ton_balance == Decimal("5")
