"""backend/deps.py — Dependencies de autenticação e autorização por papel."""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models.user import User
from backend.security import decodificar_token

# auto_error=False: não levanta se faltar o header — tentamos o cookie antes de negar.
_bearer = HTTPBearer(auto_error=False)


def usuario_atual(
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    # 1) Authorization: Bearer  → 2) cookie httpOnly "token"
    token = cred.credentials if cred else request.cookies.get("token")
    sub = decodificar_token(token) if token else None
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao autenticado",
        )
    return sub


def usuario_db(
    username: str = Depends(usuario_atual),
    db: Session = Depends(get_db),
) -> User:
    """Usuário autenticado carregado do banco. 401 se inexistente ou inativo."""
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inativo ou inexistente",
        )
    return user


def requer_papel(*roles: str):
    """Dependency que exige que o papel do usuário esteja em `roles` (senão 403)."""
    def _dep(user: User = Depends(usuario_db)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissao para esta acao",
            )
        return user
    return _dep


# Atalho: quem pode EDITAR dados (carteira/watchlist/scan/GPT). Leitor só lê.
EDITORES = ("admin", "gestor", "operador")
