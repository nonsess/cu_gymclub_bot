from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    TELEGRAM_BOT_TOKEN: str

    REDIS_URL: str

    CREATE_SEED_DATA: bool = False

    @property
    def POSTGRES_DSN(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@db:5432/{self.POSTGRES_DB}"

settings = Settings()