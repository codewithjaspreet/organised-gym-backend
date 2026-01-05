from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class Platform(str, Enum):
    ANDROID = "android"
    IOS = "ios"


class LoginRequest(BaseModel):
    email: str = Field(..., description="The user's email", pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(..., description="The user's password" , min_length=6)
    device_token: Optional[str] = Field(None, description="The device token for push notifications")
    app_version: Optional[str] = Field(None, description="The app version")
    platform: Optional[str] = Field(None, description="The platform: android or ios")
    
    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v):
        if v is not None:
            v_lower = v.lower()
            if v_lower not in ["android", "ios"]:
                raise ValueError("Platform must be either 'android' or 'ios'")
            return v_lower
        return v


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="The access token")
    refresh_token: str = Field(..., description="The refresh token")
    token_type: str = Field(..., description="The token type")
    role: str = Field(..., description="The user's role")