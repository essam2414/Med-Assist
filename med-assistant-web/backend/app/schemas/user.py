from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: EmailStr
    specialty: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    email: Optional[EmailStr] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserChangePassword(BaseModel):
    current_password: str
    new_password: str
