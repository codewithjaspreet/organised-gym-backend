from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from app.models.user import Gender, Role



class UserCreate(BaseModel):
    user_name: str
    name: str
    email: str
    password: str
    phone: str
    gender: Gender
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    dob: date
    role: Role = Role.MEMBER

class UserResponse(BaseModel):
    id: str
    user_name: str
    name: str
    email: str
    phone: str
    gender: Gender
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    created_at: datetime


