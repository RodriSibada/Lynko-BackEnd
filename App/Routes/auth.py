import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Config.database import get_db
from Config.schemas import UserRegister, UserLogin, Token, UserResponse
from Controllers.auth_controller import AuthController

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

@router.post("/register", response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Endpoint para registrar un nuevo usuario
    
    - **name**: Nombre del usuario
    - **email**: Email único
    - **password**: Contraseña
    """
    return AuthController.register(user_data, db)

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Endpoint para iniciar sesión
    
    - **email**: Email registrado
    - **password**: Contraseña
    """
    return AuthController.login(user_data, db)

@router.get("/me", response_model=UserResponse)
def get_me(token: str = None, db: Session = Depends(get_db)):
    """
    Obtener información del usuario actual
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido"
        )
    
    return AuthController.get_current_user(token, db)