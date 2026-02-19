from sqlalchemy import (
    Boolean,
    ForeignKey,
    CheckConstraint,
    Index,
    Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.models.base import BaseModel


class Match(BaseModel):
    __tablename__ = "matches"
    
    user1_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user2_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    user1 = relationship("User", foreign_keys=[user1_id], back_populates="matches_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="matches_as_user2")
    
    __table_args__ = (
        CheckConstraint("user1_id < user2_id", name="chk_matches_order"),
        Index("idx_matches_user1", "user1_id"),
        Index("idx_matches_user2", "user2_id"),
    )
    
    def __repr__(self):
        return f"<Match(user1={self.user1_id}, user2={self.user2_id})>"