from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):

    db_connection_url: str
    app_name: str 
    access_token_expire_minutes: int = 43200  # 1 month (30 days = 43,200 minutes)
    algorithm: str = "HS256"
    secret_key: str
    refresh_token_expire_days: int = 7
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


