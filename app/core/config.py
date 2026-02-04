from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Optional


class Settings(BaseSettings):
    # AWS
    aws_region: str = Field(..., env="AWS_REGION")

    # DB
    db_host: str = Field(..., env="DB_HOST")
    db_port: int = Field(..., env="DB_PORT")
    db_name: str = Field(..., env="DB_NAME")
    db_user: str = Field(..., env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")

    smtp_host: str = Field(..., env="SMTP_HOST")
    smtp_port: int = Field(..., env="SMTP_PORT")
    smtp_secure: bool = Field(False, env="SMTP_SECURE")

    smtp_user: str = Field(..., env="SMTP_USER")
    smtp_password: SecretStr = Field(..., env="SMTP_PASSWORD")

    no_reply_email: str = Field(..., env="NO_REPLY_EMAIL")
    support_email: str = Field(..., env="SUPPORT_EMAIL")


    # App / Auth
    app_name: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200
    refresh_token_expire_days: int = 7

    # Others
    subscription_grace_period_days: int = 5
    firebase_credentials: Optional[str] = None
    firebase_base_64: Optional[str] = None
    firebase_project_id: str = "app-organised-gym"
    cloudinary_url: Optional[str] = None
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_cloud_api_key: Optional[str] = None
    cloudinary_cloud_api_secret: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
