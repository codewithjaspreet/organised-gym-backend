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

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[Gender] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[Role] = None
    gym_id: Optional[str] = None

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


