# from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic import Field
# from typing import Optional


# class Settings(BaseSettings):

#     db_connection_url: str
#     app_name: str 
#     access_token_expire_minutes: int = 43200  # 1 month (30 days = 43,200 minutes)
#     algorithm: str = "HS256"
#     secret_key: str
#     refresh_token_expire_days: int = 7
#     subscription_grace_period_days: int = Field(default=5, description="Grace period in days for expired subscriptions")
#     firebase_credentials: Optional[str] = Field(default=None, description="Firebase credentials as JSON string")
#     firebase_project_id: str = Field(default="app-organised-gym", description="Firebase project ID")
#     cloudinary_url: Optional[str] = Field(default=None, description="Cloudinary URL for image uploads")
#     cloudinary_cloud_name: Optional[str] = Field(default=None, description="Cloudinary cloud name")
#     cloudinary_cloud_api_key: Optional[str] = Field(default=None, description="Cloudinary API key")
#     cloudinary_cloud_api_secret: Optional[str] = Field(default=None, description="Cloudinary API secret")
#     resend_api_key: Optional[str] = Field(default=None, description="Resend API key for email sending")
#     frontend_url: Optional[str] = Field(default="https://yourapp.com", description="Frontend URL for password reset links")
#     model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# settings = Settings()



from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):

    aws_region: str = Field(..., env="AWS_REGION")
    db_host: str = Field(..., env="DB_HOST")
    db_port: int = Field(..., env="DB_PORT")
    db_name: str = Field(..., env="DB_NAME")
    db_user: str = Field(..., env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")
    app_name: str 
    access_token_expire_minutes: int = 43200  # 1 month (30 days = 43,200 minutes)
    algorithm: str = "HS256"
    secret_key: str
    refresh_token_expire_days: int = 7
    subscription_grace_period_days: int = Field(default=5, description="Grace period in days for expired subscriptions")
    firebase_credentials: Optional[str] = Field(default=None, description="Firebase credentials as JSON string")
    firebase_project_id: str = Field(default="app-organised-gym", description="Firebase project ID")
    cloudinary_url: Optional[str] = Field(default=None, description="Cloudinary URL for image uploads")
    cloudinary_cloud_name: Optional[str] = Field(default=None, description="Cloudinary cloud name")
    cloudinary_cloud_api_key: Optional[str] = Field(default=None, description="Cloudinary API key")
    cloudinary_cloud_api_secret: Optional[str] = Field(default=None, description="Cloudinary API secret")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

