"""
Pydantic схемы для спиритов
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# Базовые схемы для SpiritTemplate
class SpiritTemplateBase(BaseModel):
    """Базовая схема шаблона спирита"""
    code: Optional[str] = None
    element_id: Optional[int] = None
    rarity_id: Optional[int] = None
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    generation: int = Field(default=1, description="Поколение (1-7+)")
    default_level: int = Field(default=1, description="Начальный уровень")
    default_xp_for_next: int = Field(default=100, description="XP для следующего уровня")
    description_ru: Optional[str] = None
    description_en: Optional[str] = None

    # Базовые характеристики
    base_run: int = Field(default=1, description="Бег")
    base_jump: int = Field(default=1, description="Прыжок")
    base_swim: int = Field(default=1, description="Плавание")
    base_dives: int = Field(default=1, description="Ныряние")
    base_fly: int = Field(default=1, description="Полёт")
    base_maneuver: int = Field(default=1, description="Маневрирование")
    base_max_energy: int = Field(default=100, description="Максимальная энергия")

    icon_url: Optional[str] = None
    spirit_animation_url: Optional[str] = None
    capsule_id: Optional[int] = None
    is_starter: bool = Field(default=False, description="Стартовый спирит")
    is_available: bool = Field(default=True, description="Доступен для выпадения")


class SpiritTemplateCreate(SpiritTemplateBase):
    """Схема для создания шаблона спирита (admin)"""
    code: str = Field(..., description="Уникальный код спирита")
    element_id: int
    rarity_id: int
    name_ru: str
    name_en: str


class SpiritTemplateUpdate(BaseModel):
    """Схема для обновления шаблона спирита (admin)"""
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    base_run: Optional[int] = None
    base_jump: Optional[int] = None
    base_swim: Optional[int] = None
    base_dives: Optional[int] = None
    base_fly: Optional[int] = None
    base_maneuver: Optional[int] = None
    base_max_energy: Optional[int] = None
    icon_url: Optional[str] = None
    spirit_animation_url: Optional[str] = None
    is_available: Optional[bool] = None


class SpiritTemplateResponse(SpiritTemplateBase):
    """Схема ответа для шаблона спирита"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Базовые схемы для PlayerSpirit
class PlayerSpiritBase(BaseModel):
    """Базовая схема спирита игрока"""
    spirit_template_id: Optional[int] = None
    custom_name: Optional[str] = Field(None, description="Кастомное имя")
    generation: int = Field(default=1)
    level: int = Field(default=1)
    xp_for_next_level: int = Field(default=100)
    xp: int = Field(default=0)
    description_ru: Optional[str] = None
    description_en: Optional[str] = None

    # Характеристики
    base_run: int = Field(default=1)
    base_jump: int = Field(default=1)
    base_swim: int = Field(default=1)
    base_dives: int = Field(default=1)
    base_fly: int = Field(default=1)
    base_maneuver: int = Field(default=1)
    base_max_energy: int = Field(default=100)
    energy: int = Field(default=100, description="Текущая энергия")

    # Игровое состояние
    is_active: bool = Field(default=False, description="Активен в партии")
    slot_id: Optional[int] = None

    # NFT статус
    is_minted: bool = Field(default=False, description="Смитнчен ли как NFT")
    nft_id: Optional[str] = None


class PlayerSpiritResponse(PlayerSpiritBase):
    """Схема ответа для спирита игрока"""
    id: int
    owner_id: int
    acquired_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Схемы для действий со спиритами
class SpiritActivateRequest(BaseModel):
    """Схема запроса на активацию спирита в слоте"""
    player_spirit_id: int = Field(..., description="ID спирита игрока")
    player_slot_id: int = Field(..., description="ID слота для активации")


class SpiritRenameRequest(BaseModel):
    """Схема запроса на переименование спирита"""
    player_spirit_id: int = Field(..., description="ID спирита игрока")
    custom_name: str = Field(..., min_length=1, max_length=50, description="Новое имя")


class SpiritMintRequest(BaseModel):
    """Схема запроса на минт спирита как NFT"""
    player_spirit_id: int = Field(..., description="ID спирита игрока")
    pay_with: str = Field(default="ton", description="Валюта оплаты (ton)")


class SpiritBreedRequest(BaseModel):
    """Схема запроса на скрещивание спиритов"""
    parent1_id: int = Field(..., description="ID первого родителя")
    parent2_id: int = Field(..., description="ID второго родителя")
    pay_with: str = Field(default="ton", description="Валюта оплаты (ton)")


class SpiritBreedResponse(BaseModel):
    """Схема ответа на скрещивание"""
    child_spirit: PlayerSpiritResponse
    balance_change: Decimal = Field(..., description="Изменение баланса")
    currency: str
    message: str


class SpiritRestoreEnergyRequest(BaseModel):
    """Схема запроса на мгновенное восстановление энергии"""
    pay_with: str = Field(default="lumens", description="Валюта оплаты (ton или lumens)")


class SpiritRestoreEnergyResponse(BaseModel):
    """Схема ответа на восстановление энергии"""
    spirit: PlayerSpiritResponse
    previous_energy: int = Field(..., description="Предыдущий уровень энергии")
    new_energy: int = Field(..., description="Новый уровень энергии")
    max_energy: int = Field(..., description="Максимальная энергия")
    balance_change: Decimal = Field(..., description="Изменение баланса")
    currency: str
