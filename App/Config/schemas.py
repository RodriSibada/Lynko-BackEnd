from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Esquema para registro
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

# Esquema para login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Esquema para respuesta de usuario (sin contraseña)
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    xp: int
    level: int
    created_at: datetime

    class Config:
        from_attributes = True

# Esquema para token JWT
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse