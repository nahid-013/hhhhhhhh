"""
Pydantic схемы для авторизации
"""
from pydantic import BaseModel
from typing import Optional


class TelegramAuthData(BaseModel):
    """Данные Telegram авторизации"""

    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class LoginRequest(BaseModel):
    """Запрос на логин через Telegram"""

    init_data: str
    referral_code: Optional[str] = None


class LoginResponse(BaseModel):
    """Ответ на логин"""

    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = False


class TokenData(BaseModel):
    """Данные из JWT токена"""

    tg_id: int
    username: Optional[str] = None


class WalletConnectRequest(BaseModel):
    """Запрос на подключение кошелька"""

    address: str


class WithdrawalRequest(BaseModel):
    """Запрос на вывод средств"""

    amount: str  # Decimal передается как строка
    currency: str  # "TON" или "LUMENS"


class WithdrawalResponse(BaseModel):
    """Ответ о выводе средств"""

    id: int
    tg_id: int
    amount: str
    currency: str
    status: str
    created_at: str

    class Config:
        from_attributes = True
