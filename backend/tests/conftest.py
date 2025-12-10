"""
Pytest конфигурация и общие фикстуры
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from backend.db.base_class import Base
from backend.core.config import settings

# Импорт всех моделей для создания таблиц
from backend.db.models import (
    Element,
    Rarity,
    User,
    Wallet,
    Ban,
    Donation,
    BalanceLog,
    Withdrawal,
)


# Тестовая база данных
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Создает тестовую базу данных для каждого теста
    """
    # Создание engine для тестовой БД
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Создание всех таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создание session maker
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Создание сессии
    async with async_session() as session:
        yield session

    # Очистка после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def test_user_data():
    """Тестовые данные пользователя"""
    return {
        "tg_id": 123456789,
        "user_name": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "ton_address": None,
        "ton_balance": 0,
        "lumens_balance": 1000,
    }
