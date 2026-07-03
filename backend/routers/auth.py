"""backend/routers/auth.py — POST /auth/login: valida credenciais e emite JWT."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models.user import User
from backend.schemas.auth import LoginRequest, TokenResponse
from backend.security import criar_access_token, verificar_senha

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_MAX_AGE = 86400 * 7   # 7 dias
# secure=False enquanto for HTTP; virar True quando tiver HTTPS (Agente 11).


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == dados.username).first()
    if not user or not verificar_senha(dados.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    token = criar_access_token(user.username)
    # Cookie httpOnly: o browser reenvia automático nas chamadas /api/ (deps lê como fallback).
    response.set_cookie(
        key="token", value=token, httponly=True,
        max_age=_COOKIE_MAX_AGE, samesite="lax", secure=False,
    )
    # Mantém o access_token no corpo — não quebra nenhum consumidor Bearer existente.
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="token", samesite="lax")
    return {"status": "logout"}
