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
    cloudinary_url: Optional[str] = Field(default=None, description="Cloudinary URL for image uploads")
    cloudinary_cloud_name: Optional[str] = Field(default=None, description="Cloudinary cloud name")
    cloudinary_cloud_api_key: Optional[str] = Field(default=None, description="Cloudinary API key")
    cloudinary_cloud_api_secret: Optional[str] = Field(default=None, description="Cloudinary API secret")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


