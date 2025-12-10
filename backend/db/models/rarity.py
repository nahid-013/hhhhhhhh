"""
Модель редкостей (rarities)
"""
from sqlalchemy import Column, Integer, String, Text, Numeric
from sqlalchemy.orm import relationship
from backend.db.base_class import Base


class Rarity(Base):
    """Редкости спиритов (common, rare, epic, legendary, mythical)"""

    __tablename__ = "rarities"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name_ru = Column(Text, nullable=True)
    name_en = Column(Text, nullable=True)
    icon_url = Column(Text, nullable=True)
    power_factor = Column(Numeric, default=1.0, nullable=False)

    # Relationships
    capsule_templates = relationship("CapsuleTemplate", back_populates="rarity")
    spirit_templates = relationship("SpiritTemplate", back_populates="rarity")
