"""backend/routers/auth.py — login/logout, /me e troca de senha."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.deps import usuario_db
from backend.models.user import User
from backend.schemas.auth import LoginRequest, TokenResponse
from backend.security import criar_access_token, hash_senha, verificar_senha

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_MAX_AGE = 86400 * 7   # 7 dias
# secure=False enquanto for HTTP; virar True quando tiver HTTPS (Agente 11).


class TrocaSenha(BaseModel):
    senha_atual: str
    senha_nova: str


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == dados.username).first()
    if not user or not verificar_senha(dados.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desativado",
        )
    user.last_login = func.now()
    db.commit()
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


@router.get("/me")
def me(user: User = Depends(usuario_db)):
    return {"username": user.username, "role": user.role, "active": bool(user.active)}


@router.post("/change-password")
def change_password(dados: TrocaSenha, db: Session = Depends(get_db),
                    user: User = Depends(usuario_db)):
    if not verificar_senha(dados.senha_atual, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Senha atual incorreta")
    if len(dados.senha_nova) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Senha nova muito curta (mín. 6)")
    user.password_hash = hash_senha(dados.senha_nova)
    db.commit()
    return {"ok": True}
