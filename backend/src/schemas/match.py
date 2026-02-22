from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class MatchResponse(BaseModel):
    id: int = Field(..., description="ID матча")
    user1_id: int = Field(..., description="ID первого пользователя")
    user2_id: int = Field(..., description="ID второго пользователя")
    created_at: datetime = Field(..., description="Время создания матча")
    
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 1,
            "user1_id": 100,
            "user2_id": 200,
            "created_at": "2024-02-19T18:30:00"
        }
    })


class MatchDetailResponse(BaseModel):
    id: int = Field(..., description="ID матча")
    matched_user_id: int = Field(..., description="ID пользователя, с которым матч")
    matched_user_username: Optional[str] = Field(None, description="Юзернейм пользователя")
    matched_user_first_name: Optional[str] = Field(None, description="Имя пользователя")
    created_at: datetime = Field(..., description="Время создания матча")
    contact_revealed: bool = Field(..., description="Показан ли контакт")
    
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 1,
            "matched_user_id": 200,
            "matched_user_username": "@gymbro",
            "matched_user_first_name": "Alex",
            "created_at": "2024-02-19T18:30:00",
            "contact_revealed": True
        }
    })


class MatchContactResponse(BaseModel):
    telegram_id: str = Field(..., description="Telegram ID пользователя")
    username: Optional[str] = Field(None, description="Юзернейм (@username)")
    first_name: Optional[str] = Field(None, description="Имя")
    link: str = Field(..., description="Прямая ссылка для написания (t.me/... или tg://user?id=...)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "telegram_id": "123456789",
            "username": "@gymbro",
            "first_name": "Alex",
            "link": "https://t.me/gymbro"
        }
    })