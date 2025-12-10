"""
Модели для спиритов (Spirits)
"""
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship

from backend.db.base_class import Base


class SpiritTemplate(Base):
    """
    Шаблон спирита - описывает базовые характеристики спирита
    """
    __tablename__ = "spirits_template"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    element_id = Column(Integer, ForeignKey("elements.id"))
    rarity_id = Column(Integer, ForeignKey("rarities.id"))
    name_ru = Column(String)
    name_en = Column(String)
    generation = Column(Integer, default=1, server_default="1")  # Поколение (1-7+)
    default_level = Column(Integer, default=1, server_default="1")  # Начальный уровень
    default_xp_for_next = Column(Integer, default=100, server_default="100")  # XP для следующего уровня
    description_ru = Column(String)
    description_en = Column(String)

    # Базовые характеристики (stats)
    base_run = Column(Integer, default=1, server_default="1")  # Бег
    base_jump = Column(Integer, default=1, server_default="1")  # Прыжок
    base_swim = Column(Integer, default=1, server_default="1")  # Плавание
    base_dives = Column(Integer, default=1, server_default="1")  # Ныряние
    base_fly = Column(Integer, default=1, server_default="1")  # Полёт
    base_maneuver = Column(Integer, default=1, server_default="1")  # Маневрирование
    base_max_energy = Column(Integer, default=100, server_default="100")  # Максимальная энергия

    icon_url = Column(String)
    spirit_animation_url = Column(String)
    capsule_id = Column(Integer, ForeignKey("capsule_template.id"))  # Из какой капсулы можно получить
    is_starter = Column(Boolean, default=False, server_default="false")  # Стартовый спирит
    is_available = Column(Boolean, default=True, server_default="true", index=True)  # Доступен для выпадения
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    # Relationships
    element = relationship("Element", back_populates="spirit_templates")
    rarity = relationship("Rarity", back_populates="spirit_templates")
    capsule = relationship("CapsuleTemplate", back_populates="spirit_templates")
    player_spirits = relationship("PlayerSpirit", back_populates="template")
    capsule_drops = relationship("CapsuleDrop", back_populates="spirit_template")


class PlayerSpirit(Base):
    """
    Спирит игрока - NFT существо с уникальными характеристиками
    """
    __tablename__ = "player_spirits"

    id = Column(BigInteger, primary_key=True, index=True)
    owner_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), index=True)
    spirit_template_id = Column(Integer, ForeignKey("spirits_template.id", ondelete="SET NULL"))
    custom_name = Column(String)  # Кастомное имя от игрока
    generation = Column(Integer, default=1, server_default="1")
    level = Column(Integer, default=1, server_default="1")
    xp_for_next_level = Column(Integer, default=100, server_default="100")
    xp = Column(Integer, default=0, server_default="0")
    description_ru = Column(String)
    description_en = Column(String)

    # Характеристики (копируются из template и могут улучшаться)
    base_run = Column(Integer, default=1, server_default="1")
    base_jump = Column(Integer, default=1, server_default="1")
    base_swim = Column(Integer, default=1, server_default="1")
    base_dives = Column(Integer, default=1, server_default="1")
    base_fly = Column(Integer, default=1, server_default="1")
    base_maneuver = Column(Integer, default=1, server_default="1")
    base_max_energy = Column(Integer, default=100, server_default="100")
    energy = Column(Integer, default=100, server_default="100")  # Текущая энергия

    # Игровое состояние
    is_active = Column(Boolean, default=False, server_default="false", index=True)  # Активен в партии
    slot_id = Column(BigInteger, ForeignKey("player_slots.id"))  # В каком слоте находится

    # NFT статус
    is_minted = Column(Boolean, default=False, server_default="false")  # Смитнчен ли как NFT
    nft_id = Column(String)  # ID токена в blockchain

    acquired_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    # Relationships
    owner = relationship("User", back_populates="spirits")
    template = relationship("SpiritTemplate", back_populates="player_spirits")
    slot = relationship("PlayerSlot", back_populates="spirit")
