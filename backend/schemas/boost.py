"""
Pydantic схемы для бустов
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Базовые схемы для BoostTemplate
class BoostTemplateBase(BaseModel):
    """Базовая схема шаблона буста"""
    internal_name: Optional[str] = None
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    price_ton: Decimal = Field(default=Decimal("0"), description="Цена в TON")
    boost_xp: int = Field(default=0, description="Количество XP которое даёт буст")
    amount: int = Field(default=0, description="Количество в наличии (0 = безлимит)")
    icon_url: Optional[str] = None
    is_available: bool = Field(default=True, description="Доступен для покупки")
    sort_order: Optional[int] = Field(default=0, description="Порядок отображения в магазине")


class BoostTemplateCreate(BoostTemplateBase):
    """Схема для создания шаблона буста (admin)"""
    internal_name: str = Field(..., description="Внутреннее название буста")
    name_ru: str
    name_en: str
    boost_xp: int = Field(..., gt=0, description="XP буста должен быть больше 0")


class BoostTemplateUpdate(BaseModel):
    """Схема для обновления шаблона буста (admin)"""
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    price_ton: Optional[Decimal] = None
    boost_xp: Optional[int] = None
    amount: Optional[int] = None
    icon_url: Optional[str] = None
    is_available: Optional[bool] = None
    sort_order: Optional[int] = None


class BoostTemplateResponse(BoostTemplateBase):
    """Схема ответа для шаблона буста"""
    id: int

    model_config = ConfigDict(from_attributes=True)


# Базовые схемы для PlayerBoost
class PlayerBoostBase(BaseModel):
    """Базовая схема буста игрока"""
    boost_id: Optional[int] = None
    quantity: int = Field(default=1, description="Количество таких бустов")


class PlayerBoostResponse(PlayerBoostBase):
    """Схема ответа для буста игрока"""
    id: int
    owner_id: int
    acquired_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Схемы для действий с бустами
class BoostBuyRequest(BaseModel):
    """Схема запроса на покупку буста"""
    boost_id: int = Field(..., description="ID шаблона буста")
    quantity: int = Field(default=1, ge=1, le=100, description="Количество бустов для покупки")
    pay_with: str = Field(default="ton", description="Валюта оплаты (ton/lumens)")


class BoostUseRequest(BaseModel):
    """Схема запроса на использование буста"""
    player_boost_id: int = Field(..., description="ID буста игрока")
    player_spirit_id: int = Field(..., description="ID спирита, на которого применяется буст")


class BoostBuyResponse(BaseModel):
    """Схема ответа на покупку буста"""
    player_boost: PlayerBoostResponse
    balance_change: Decimal = Field(..., description="Изменение баланса")
    currency: str
