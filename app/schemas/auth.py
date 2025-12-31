from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="The user's email", pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(..., description="The user's password" , min_length=6)


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="The access token")
    refresh_token: str = Field(..., description="The refresh token")
    token_type: str = Field(..., description="The token type")