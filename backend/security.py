"""
backend/security.py — Hash de senha (bcrypt via passlib) e emissão de JWT.
bcrypt fixado em 4.0.1 no VPS (passlib 1.7.4 não suporta bcrypt 4.1+/5.x).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import JWT_ALG, JWT_EXPIRE_MINUTES, JWT_SECRET

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    return _pwd.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return _pwd.verify(senha, senha_hash)
    except ValueError:
        return False


def criar_access_token(sub: str) -> str:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": agora,
        "exp": agora + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decodificar_token(token: str) -> str | None:
    """Retorna o 'sub' se o token for válido e não expirado, senão None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        return None
    return payload.get("sub")
