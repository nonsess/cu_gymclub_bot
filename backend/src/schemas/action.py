from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from datetime import datetime
from typing import List, Optional

class ActionType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    REPORT = "report"

class ActionCreate(BaseModel):
    to_user_id: int = Field(..., gt=0, description="ID пользователя, которому отправляется действие")
    action_type: ActionType = Field(..., description="Тип действия")
    report_reason: Optional[str] = Field(None, max_length=200, description="Причина жалобы (только для report)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "to_user_id": 123,
            "action_type": "like",
            "report_reason": None
        }
    })

class ActionResponse(BaseModel):
    is_match: bool = Field(..., description="True, если произошёл взаимный лайк (матч)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "is_match": True
        }
    })


class IncomingLikeResponse(BaseModel):
    from_user_id: int = Field(..., description="ID пользователя, который лайкнул")
    created_at: datetime = Field(..., description="Время лайка")
    
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "from_user_id": 123,
            "created_at": "2024-02-19T18:30:00"
        }
    })


class IncomingLikesList(BaseModel):
    items: List[IncomingLikeResponse]
    total: int = Field(..., description="Количество входящих лайков")