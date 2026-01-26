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
    firebase_service_account_json_base64: Optional[str] = None
    firebase_project_id: str = Field(default="app-organised-gym", description="Firebase project ID")
    cloudinary_url: Optional[str] = Field(default=None, description="Cloudinary URL for image uploads")
    cloudinary_cloud_name: Optional[str] = Field(default=None, description="Cloudinary cloud name")
    cloudinary_cloud_api_key: Optional[str] = Field(default=None, description="Cloudinary API key")
    cloudinary_cloud_api_secret: Optional[str] = Field(default=None, description="Cloudinary API secret")
    # Email configuration
    smtp_host: Optional[str] = Field(default=None, description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_from_email: Optional[str] = Field(default=None, description="Email address to send from")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    frontend_url: Optional[str] = Field(default=None, description="Frontend URL for password reset links")
    password_reset_token_expire_hours: int = Field(default=1, description="Password reset token expiration in hours")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


