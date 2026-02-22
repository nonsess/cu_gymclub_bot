from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Имя")
    description: str = Field(..., min_length=10, max_length=1000, description="Описание анкеты")
    gender: GenderEnum = Field(..., description="Пол: male, female, other")
    age: Optional[int] = Field(None, ge=16, le=100, description="Возраст")
    photo_ids: Optional[List[str]] = Field(default_factory=list, description="Telegram file_id фотографий")
    
    model_config = ConfigDict(
    json_schema_extra={
        "example": {
            "description": "Люблю кроссфит, ищу напарника для приседа. Тренируюсь 3 раза в неделю.",
            "gender": "male",
            "age": 22,
            "photo_ids": ["AgACAgIA..."]
        }
    })


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Имя")
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    age: Optional[int] = Field(None, ge=16, le=100)
    photo_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "description": "Обновленное описание...",
            "age": 23,
            "is_active": True
        }
    })


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: str
    gender: str
    age: Optional[int]
    photo_ids: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )