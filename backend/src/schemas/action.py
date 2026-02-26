from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Optional

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
