from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr


class UserCreate(UserBase):
    """Model for user registration"""
    password: str = Field(..., min_length=8)
    role: UserRole = Field(default=UserRole.VIEWER)


class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr
    password: str


class User(UserBase):
    """Full user model"""
    id: UUID = Field(default_factory=uuid4)
    role: UserRole = UserRole.VIEWER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model as stored in database"""
    password_hash: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Data encoded in JWT token"""
    user_id: str
    email: Optional[str] = None
    role: Optional[str] = None
