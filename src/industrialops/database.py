"""SQLAlchemy declarative base shared by IndustrialOps persistence models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for IndustrialOps database tables."""
