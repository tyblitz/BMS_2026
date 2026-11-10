from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    role: str # 'school', 'sdo', 'region', 'admin'
    school_name: Optional[str] = None
    division: Optional[str] = None
    region: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    school_name: Optional[str] = None
    division: Optional[str] = None
    region: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: str
    created_on: datetime
    created_by: str

    model_config = ConfigDict(from_attributes=True)



class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    school_name: Optional[str] = None
    division: Optional[str] = None
    region: Optional[str] = None
