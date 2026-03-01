from sqlalchemy import Boolean, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    telegram_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sent_actions = relationship("UserAction", foreign_keys="UserAction.from_user_id", back_populates="from_user", cascade="all, delete-orphan")
    received_actions = relationship("UserAction", foreign_keys="UserAction.to_user_id", back_populates="to_user", cascade="all, delete-orphan")
    matches_as_user1 = relationship("Match", foreign_keys="Match.user1_id", back_populates="user1", cascade="all, delete-orphan")
    matches_as_user2 = relationship("Match", foreign_keys="Match.user2_id", back_populates="user2", cascade="all, delete-orphan")
    
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id})>"