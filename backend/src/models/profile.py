from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Index,
    Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from pgvector.sqlalchemy import Vector
import enum

from src.models.base import BaseModel


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"


class Profile(BaseModel):
    __tablename__ = "profiles"
        
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    name: Mapped[str] =  mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    gender: Mapped[GenderEnum | None] = mapped_column(ENUM(GenderEnum, name="gender_enum", create_type=True), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True, default=list)
    embedding: Mapped[list | None] = mapped_column(Vector(384), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    user = relationship("User", back_populates="profile")
    
    __table_args__ = (
        Index("idx_profiles_gender", "gender"),
        Index("idx_profiles_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<Profile(id={self.id}, user_id={self.user_id})>"
