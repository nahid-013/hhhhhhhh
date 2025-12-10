"""
Pydantic схемы для пользователей
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class UserBase(BaseModel):
    """Базовая схема пользователя"""

    user_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: Optional[str] = None


class UserCreate(UserBase):
    """Схема создания пользователя"""

    tg_id: int
    referral_code: str
    referraled_by: Optional[int] = None


class UserUpdate(BaseModel):
    """Схема обновления профиля"""

    user_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: Optional[str] = None


class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""

    tg_id: int
    ton_address: Optional[str] = None
    ton_balance: Decimal = Field(default=Decimal("0"))
    lumens_balance: Decimal = Field(default=Decimal("1000"))
    referral_code: str
    referraled_by: Optional[int] = None
    referrals_count: int = 0
    is_banned: bool = False
    is_admin: bool = False
    donate_amount: Decimal = Field(default=Decimal("0"))
    created_at: datetime
    updated_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True


class WalletConnect(BaseModel):
    """Схема подключения TON кошелька"""

    address: str
    proof: Optional[str] = None


class WalletResponse(BaseModel):
    """Схема ответа кошелька"""

    id: int
    tg_id: int
    address: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReferralInfo(BaseModel):
    """Информация о реферале"""

    tg_id: int
    user_name: Optional[str] = None
    first_name: Optional[str] = None
    created_at: datetime
    donate_amount: Decimal

    class Config:
        from_attributes = True


class WithdrawalCreate(BaseModel):
    """Схема создания вывода средств"""

    amount: Decimal
    currency: str = "TON"


class WithdrawalResponse(BaseModel):
    """Схема ответа вывода средств"""

    id: int
    tg_id: int
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
