"""
Тесты для auth endpoints
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.repository import user as user_repo
from backend.schemas.user import UserCreate
from backend.core.security import create_access_token, generate_referral_code


@pytest.mark.asyncio
async def test_create_user(test_db: AsyncSession):
    """Тест создания нового пользователя"""
    tg_id = 123456789
    referral_code = generate_referral_code(tg_id)

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

    assert user.tg_id == tg_id
    assert user.user_name == "testuser"
    assert user.referral_code == referral_code
    assert user.lumens_balance == 1000
    assert user.ton_balance == 0


@pytest.mark.asyncio
async def test_get_user_by_tg_id(test_db: AsyncSession):
    """Тест получения пользователя по tg_id"""
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

    # Получаем пользователя
    user = await user_repo.get_user_by_tg_id(test_db, tg_id)

    assert user is not None
    assert user.tg_id == tg_id
    assert user.user_name == "testuser"


@pytest.mark.asyncio
async def test_referral_system(test_db: AsyncSession):
    """Тест реферальной системы"""
    # Создаем реферера
    referrer_tg_id = 111111111
    referrer_code = generate_referral_code(referrer_tg_id)
    referrer_data = UserCreate(
        tg_id=referrer_tg_id,
        user_name="referrer",
        first_name="Referrer",
        last_name="User",
        language="ru",
        referral_code=referrer_code,
        referraled_by=None,
    )
    referrer = await user_repo.create_user(test_db, referrer_data)
    initial_balance = referrer.lumens_balance

    # Создаем реферала
    referral_tg_id = 222222222
    referral_code = generate_referral_code(referral_tg_id)
    referral_data = UserCreate(
        tg_id=referral_tg_id,
        user_name="referral",
        first_name="Referral",
        last_name="User",
        language="ru",
        referral_code=referral_code,
        referraled_by=referrer_tg_id,
    )
    referral = await user_repo.create_user(test_db, referral_data)

    # Проверяем, что реферал привязан
    assert referral.referraled_by == referrer_tg_id

    # Получаем обновленного реферера
    updated_referrer = await user_repo.get_user_by_tg_id(test_db, referrer_tg_id)

    # Проверяем, что счетчик рефералов увеличился
    assert updated_referrer.referrals_count == 1

    # Проверяем, что реферер получил бонус
    assert updated_referrer.lumens_balance > initial_balance


@pytest.mark.asyncio
async def test_jwt_token_creation():
    """Тест создания JWT токена"""
    tg_id = 123456789
    username = "testuser"

    token = create_access_token(data={"sub": tg_id, "username": username})

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_referral_code_generation():
    """Тест генерации реферального кода"""
    tg_id = 123456789

    code = generate_referral_code(tg_id)

    assert code is not None
    assert isinstance(code, str)
    assert len(code) == 8
    assert code.isupper()
