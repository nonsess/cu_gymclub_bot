from pydantic import BaseModel, Field, ConfigDict


class UserRegister(BaseModel):
    telegram_id: str = Field(..., description="Telegram ID пользователя")
    username: str = Field(None, description="Юзернейм Telegram")
    first_name: str = Field(None, description="Имя пользователя")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "telegram_id": "123456789",
            "username": "@gymbro",
            "first_name": "Alex"
        }
    })