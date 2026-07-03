"""backend/routers/auth.py — POST /auth/login: valida credenciais e emite JWT."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models.user import User
from backend.schemas.auth import LoginRequest, TokenResponse
from backend.security import criar_access_token, verificar_senha

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == dados.username).first()
    if not user or not verificar_senha(dados.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    return TokenResponse(access_token=criar_access_token(user.username))
