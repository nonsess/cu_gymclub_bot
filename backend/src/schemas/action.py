from pydantic import BaseModel, Field
from src.models.action import ActionTypeEnum
from src.schemas.profile import ProfileResponse
from typing import Optional

class ActionCreate(BaseModel):
    to_user_id: int = Field(None, description="ID пользователя, которому отправляется действие (не требуется для ответа на входящий лайк)")
    action_type: ActionTypeEnum
    report_reason: Optional[str] = Field(None, max_length=200)

class ActionResponse(BaseModel):
    action_id: int
    success: bool = True

class IncomingLikeResponse(ProfileResponse):
    incoming_action_id: int = Field(..., description="ID действия (лайка), на который нужно ответить")

class DecideOnIncomingRequest(BaseModel):
    action_id: int = Field(..., description="ID входящего лайка")
    decision: ActionTypeEnum = Field(..., description="Решение: like, dislike или report")
    report_reason: Optional[str] = Field(None, max_length=200, description="Причина жалобы (только для report)")

class DecideOnIncomingResponse(BaseModel):
    success: bool = True
    match_id: Optional[int] = Field(None, description="ID созданного матча (если решение было like)")