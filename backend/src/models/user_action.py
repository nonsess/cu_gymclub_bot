from sqlalchemy import (
    String,
    ForeignKey,
    CheckConstraint,
    Index,
    Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM
import enum

from src.models.base import BaseModel


class ActionTypeEnum(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    REPORT = "report"


class UserAction(BaseModel):
    __tablename__ = "user_actions"
        
    from_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    to_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    action_type: Mapped[ActionTypeEnum] = mapped_column(
        ENUM(ActionTypeEnum, name="action_type_enum", create_type=True), 
        nullable=False
    )
    report_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="sent_actions")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_actions")
    
    __table_args__ = (
        CheckConstraint("from_user_id != to_user_id", name="chk_actions_not_self"),
        Index("idx_actions_from_user", "from_user_id"),
        Index("idx_actions_to_user", "to_user_id"),
        Index("idx_actions_type", "action_type"),
    )
    
    def __repr__(self):
        return f"<UserAction(from={self.from_user_id} {self.action_type.value} {self.to_user_id})>"

