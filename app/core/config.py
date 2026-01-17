from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):

    db_connection_url: str
    app_name: str 
    access_token_expire_minutes: int = 43200  # 1 month (30 days = 43,200 minutes)
    algorithm: str = "HS256"
    secret_key: str
    refresh_token_expire_days: int = 7
    firebase_project_id: str = Field(default="app-organised-gym", description="Firebase project ID")
    firebase_service_account_path: Optional[str] = Field(default=None, description="Firebase service account path")
    firebase_credentials_path: Optional[str] = Field(default=None, description="Firebase credentials path (alias for firebase_service_account_path)")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


