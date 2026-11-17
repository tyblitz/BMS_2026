from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, model_validator


class UserRole(str, Enum):
    ADMIN = "admin"
    REGION = "region"
    SDO = "sdo"
    SCHOOL = "school"


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    role: UserRole
    school_name: Optional[str] = None
    division: Optional[str] = None
    region: Optional[str] = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_scope_for_role(self):
        if self.role == UserRole.SCHOOL:
            if not self.school_name:
                raise ValueError("school_name is required for school role")
            if not self.division:
                raise ValueError("division is required for school role")
            if not self.region:
                raise ValueError("region is required for school role")
        elif self.role == UserRole.SDO:
            if not self.division:
                raise ValueError("division is required for sdo role")
            if not self.region:
                raise ValueError("region is required for sdo role")
        elif self.role == UserRole.REGION:
            if not self.region:
                raise ValueError("region is required for region role")
        return self


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
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
