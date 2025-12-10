"""
Pydantic схемы для слотов
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Базовые схемы для SlotTemplate
class SlotTemplateBase(BaseModel):
    """Базовая схема шаблона слота"""
    element_id: Optional[int] = None
    price_lumens: Decimal = Field(default=Decimal("0"), description="Цена покупки в Lumens")
    sell_price_lumens: Decimal = Field(default=Decimal("0"), description="Цена продажи в Lumens")
    is_starter: bool = Field(default=False, description="Стартовый слот")
    icon_url: Optional[str] = None
    is_available: bool = Field(default=True, description="Доступен для покупки")


class SlotTemplateCreate(SlotTemplateBase):
    """Схема для создания шаблона слота (admin)"""
    element_id: int


class SlotTemplateUpdate(BaseModel):
    """Схема для обновления шаблона слота (admin)"""
    element_id: Optional[int] = None
    price_lumens: Optional[Decimal] = None
    sell_price_lumens: Optional[Decimal] = None
    icon_url: Optional[str] = None
    is_available: Optional[bool] = None


class SlotTemplateResponse(SlotTemplateBase):
    """Схема ответа для шаблона слота"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Базовые схемы для PlayerSlot
class PlayerSlotBase(BaseModel):
    """Базовая схема слота игрока"""
    slot_template_id: Optional[int] = None
    element_id: Optional[int] = None


class PlayerSlotResponse(PlayerSlotBase):
    """Схема ответа для слота игрока"""
    id: int
    owner_id: int
    acquired_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Схемы для действий со слотами
class SlotBuyRequest(BaseModel):
    """Схема запроса на покупку слота"""
    slot_template_id: int = Field(..., description="ID шаблона слота")
    pay_with: str = Field(default="lumens", description="Валюта оплаты (lumens)")


class SlotSellRequest(BaseModel):
    """Схема запроса на продажу слота"""
    player_slot_id: int = Field(..., description="ID слота игрока")


class SlotBuyResponse(BaseModel):
    """Схема ответа на покупку слота"""
    player_slot: PlayerSlotResponse
    balance_change: Decimal = Field(..., description="Изменение баланса")
    currency: str


class SlotSellResponse(BaseModel):
    """Схема ответа на продажу слота"""
    balance_change: Decimal = Field(..., description="Изменение баланса")
    currency: str
    message: str
