from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, func
from datetime import datetime

from src.db.base import Base

class TimestampMixin:    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )

class BaseModel(Base, TimestampMixin):
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True, 
        index=True
    )