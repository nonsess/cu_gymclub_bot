from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    BACKEND_URL: str = "http://backend:8000/"
    ADMIN_TELEGRAM_ID: int | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()