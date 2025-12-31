from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):

    db_connection_url: str
    app_name: str 

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


