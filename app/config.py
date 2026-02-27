from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/citizen_support"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/citizen_support"
    telegram_bot_token: str = ""
    secret_key: str = "change_me"
    debug: bool = False
    api_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
