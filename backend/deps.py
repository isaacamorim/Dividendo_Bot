"""backend/deps.py — Dependency de autenticação: exige Bearer JWT válido."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.security import decodificar_token

_bearer = HTTPBearer(auto_error=True)


def usuario_atual(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    sub = decodificar_token(cred.credentials)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado",
        )
    return sub
