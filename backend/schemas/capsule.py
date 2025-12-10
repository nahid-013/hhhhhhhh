"""
Pydantic схемы для капсул
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Базовые схемы для CapsuleTemplate
class CapsuleTemplateBase(BaseModel):
    """Базовая схема шаблона капсулы"""
    code: Optional[str] = None
    element_id: Optional[int] = None
    rarity_id: Optional[int] = None
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    open_time_seconds: int = Field(default=0, description="Время открытия в секундах")
    price_in_ton: Decimal = Field(default=Decimal("0"), description="Цена в TON")
    price_lumens: Decimal = Field(default=Decimal("0"), description="Цена в Lumens")
    icon_url: Optional[str] = None
    capsule_animation_url: Optional[str] = None
    is_available: bool = Field(default=True, description="Доступна для покупки")
    amount: int = Field(default=0, description="Количество в наличии (0 = безлимит)")
    fast_open_cost: Decimal = Field(default=Decimal("0"), description="Стоимость быстрого открытия")


class CapsuleTemplateCreate(CapsuleTemplateBase):
    """Схема для создания шаблона капсулы (admin)"""
    code: str = Field(..., description="Уникальный код капсулы")
    element_id: int
    rarity_id: int
    name_ru: str
    name_en: str


class CapsuleTemplateUpdate(BaseModel):
    """Схема для обновления шаблона капсулы (admin)"""
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    open_time_seconds: Optional[int] = None
    price_in_ton: Optional[Decimal] = None
    price_lumens: Optional[Decimal] = None
    icon_url: Optional[str] = None
    capsule_animation_url: Optional[str] = None
    is_available: Optional[bool] = None
    amount: Optional[int] = None
    fast_open_cost: Optional[Decimal] = None


class CapsuleTemplateResponse(CapsuleTemplateBase):
    """Схема ответа для шаблона капсулы"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Базовые схемы для PlayerCapsule
class PlayerCapsuleBase(BaseModel):
    """Базовая схема капсулы игрока"""
    capsule_id: Optional[int] = None
    quantity: int = Field(default=1, description="Количество таких капсул")
    is_opened: bool = Field(default=False)
    is_opening: bool = Field(default=False, description="В процессе открытия")


class PlayerCapsuleResponse(PlayerCapsuleBase):
    """Схема ответа для капсулы игрока"""
    id: int
    owner_id: int
    opening_started_at: Optional[datetime] = None
    opening_ends_at: Optional[datetime] = None
    acquired_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Схемы для действий с капсулами
class CapsuleBuyRequest(BaseModel):
    """Схема запроса на покупку капсулы"""
    capsule_id: int = Field(..., description="ID шаблона капсулы")
    quantity: int = Field(default=1, ge=1, le=100, description="Количество капсул для покупки")
    pay_with: str = Field(default="lumens", description="Валюта оплаты (ton/lumens)")


class CapsuleOpenRequest(BaseModel):
    """Схема запроса на открытие капсулы"""
    player_capsule_id: int = Field(..., description="ID капсулы игрока")


class CapsuleFastOpenRequest(BaseModel):
    """Схема запроса на быстрое открытие капсулы"""
    player_capsule_id: int = Field(..., description="ID капсулы игрока")
    pay_with: str = Field(default="lumens", description="Валюта оплаты (ton/lumens)")


class CapsuleBuyResponse(BaseModel):
    """Схема ответа на покупку капсулы"""
    player_capsule: PlayerCapsuleResponse
    balance_change: Decimal = Field(..., description="Изменение баланса")
    currency: str
