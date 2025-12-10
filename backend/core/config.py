"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Настройки приложения"""

    # Быстрая настройка поведения для неизвестных env-переменных:
    # поменяйте extra на "forbid", если нужно снова жёстко валидировать.
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )

    # Application
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Database
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "hunt_db"
    POSTGRES_USER: str = "hunt_user"
    POSTGRES_PASSWORD: str = "hunt_password"
    DATABASE_URL: str = "postgresql+asyncpg://hunt_user:hunt_password@postgres:5432/hunt_db"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = "redis://redis:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-here-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 дней

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_SECRET: str = ""

    # TON
    TON_NETWORK: str = "testnet"
    TON_API_KEY: str = ""
    TON_WALLET_ADDRESS: str = ""
    TON_WALLET_PRIVATE_KEY: str = ""
    NFT_CONTRACT_ADDRESS: str = ""

    # Economy
    INITIAL_LUMENS_BALANCE: int = 1000
    INITIAL_TON_BALANCE: int = 0
    REFERRAL_BONUS_LUMENS: int = 1000
    REFERRAL_MILESTONE_COUNT: int = 5
    REFERRAL_MILESTONE_TON: float = 0.5

    # Security
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_FINANCIAL_PER_HOUR: int = 10
    MAX_ENERGY_RESTORE_PER_DAY: int = 5
    WITHDRAWAL_MIN_AMOUNT: int = 10
    WITHDRAWAL_DELAY_HOURS: int = 24

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://t.me"]

    # Ngrok
    NGROK_ENABLED: bool = False
    NGROK_URL: str = ""
    NGROK_AUTH_TOKEN: str = ""

    @property
    def base_url(self) -> str:
        """
        Возвращает базовый URL для API.
        Если NGROK_ENABLED=true, использует NGROK_URL.
        Иначе возвращает localhost URL.
        """
        if self.NGROK_ENABLED and self.NGROK_URL:
            return self.NGROK_URL.rstrip("/")
        return f"http://{self.APP_HOST}:{self.APP_PORT}"

    @property
    def cors_origins_with_ngrok(self) -> List[str]:
        """
        Возвращает список CORS origins, включая ngrok URL если он настроен.
        """
        origins = self.CORS_ORIGINS.copy()
        if self.NGROK_ENABLED and self.NGROK_URL:
            origins.append(self.NGROK_URL.rstrip("/"))
        return origins


settings = Settings()


# Redis client singleton
_redis_client = None


def get_redis_client():
    """
    Получить Redis клиент (singleton)

    Returns:
        Redis клиент
    """
    global _redis_client

    if _redis_client is None:
        from redis import Redis

        _redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True  # Автоматическая декодировка bytes в str
        )

    return _redis_client
