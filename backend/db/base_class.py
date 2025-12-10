"""
Базовый класс для всех моделей SQLAlchemy
"""
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""

    @declared_attr
    def __tablename__(cls) -> str:
        """Автоматическая генерация имени таблицы"""
        return cls.__name__.lower()
