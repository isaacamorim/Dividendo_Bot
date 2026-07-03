"""backend/deps.py — Dependency de autenticação: aceita Bearer JWT OU cookie httpOnly 'token'."""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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
