from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from models.base import BaseDocument

class User(BaseDocument):
    email: EmailStr
    password_hash: str
    name: str
    role: Literal['admin', 'seller', 'client'] = 'client'
    phone: Optional[str] = None
    country: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    avatar_url: Optional[str] = None
    is_approved: bool = False
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Literal['client', 'seller'] = 'client'
    phone: Optional[str] = None
    country: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    country: Optional[str] = None
    avatar_url: Optional[str] = None
    is_approved: bool
    is_active: bool
    created_at: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
