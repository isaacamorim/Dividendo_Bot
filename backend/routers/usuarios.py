"""
backend/routers/usuarios.py — Gestão de usuários (espelha o Tradeon).

GET    /users            lista (admin, gestor)
POST   /users            cria usuário (admin, gestor) — respeita assignable_roles
PATCH  /users/{id}       edita role/active/senha (admin, gestor)
DELETE /users/{id}       exclui (admin)

Proteções: não remove/rebaixa/desativa o último admin ativo; gestor não age
sobre admin/gestor nem atribui papéis fora do que pode.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.deps import requer_papel
from backend.models.user import User
from backend.security import hash_senha

router = APIRouter(prefix="/users", tags=["usuarios"])

_PAPEIS = ["admin", "gestor", "operador", "leitor"]


def _assignable(actor_role: str) -> list:
    if actor_role == "admin":
        return ["admin", "gestor", "operador", "leitor"]
    if actor_role == "gestor":
        return ["operador", "leitor"]
    return []


def _serialize(u: User) -> dict:
    return {
        "id": u.id, "username": u.username, "role": u.role, "active": bool(u.active),
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "created_by": u.created_by,
    }


def _admins_ativos(db) -> int:
    return db.query(func.count(User.id)).filter(
        User.role == "admin", User.active.is_(True)).scalar() or 0


class UsuarioCreate(BaseModel):
    username: str
    password: str
    role: str = "leitor"


class UsuarioUpdate(BaseModel):
    role: Optional[str] = None
    active: Optional[bool] = None
    password: Optional[str] = None


@router.get("")
def listar(db: Session = Depends(get_db),
           ator: User = Depends(requer_papel("admin", "gestor"))):
    users = db.query(User).order_by(User.created_at.asc()).all()
    return {"ok": True, "users": [_serialize(u) for u in users],
            "assignable": _assignable(ator.role)}


@router.post("", status_code=status.HTTP_201_CREATED)
def criar(body: UsuarioCreate, db: Session = Depends(get_db),
          ator: User = Depends(requer_papel("admin", "gestor"))):
    username = (body.username or "").strip().lower()
    if not username or len(body.password or "") < 6:
        raise HTTPException(400, "Usuário obrigatório e senha com mín. 6 caracteres")
    if body.role not in _assignable(ator.role):
        raise HTTPException(403, f'Você não pode atribuir o perfil "{body.role}"')
    if db.query(User.id).filter(User.username == username).first():
        raise HTTPException(400, "Usuário já existe")
    novo = User(username=username, password_hash=hash_senha(body.password),
                role=body.role, active=True, created_by=ator.username)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"ok": True, "user": _serialize(novo)}


@router.patch("/{user_id}")
def atualizar(user_id: int, body: UsuarioUpdate, db: Session = Depends(get_db),
              ator: User = Depends(requer_papel("admin", "gestor"))):
    alvo = db.get(User, user_id)
    if not alvo:
        raise HTTPException(404, "Usuário não encontrado")
    # Gestor não age sobre admin/gestor.
    if ator.role == "gestor" and alvo.role in ("admin", "gestor"):
        raise HTTPException(403, "Gestor não pode alterar admin ou gestor")

    if body.role is not None:
        if body.role not in _assignable(ator.role):
            raise HTTPException(403, f'Você não pode atribuir o perfil "{body.role}"')
        if alvo.role == "admin" and body.role != "admin" and _admins_ativos(db) <= 1:
            raise HTTPException(400, "Não é possível rebaixar o último admin ativo")
        alvo.role = body.role
    if body.active is not None:
        if not body.active and alvo.role == "admin" and _admins_ativos(db) <= 1:
            raise HTTPException(400, "Não é possível desativar o último admin ativo")
        alvo.active = body.active
    if body.password is not None:
        if len(body.password) < 6:
            raise HTTPException(400, "Senha muito curta (mín. 6)")
        alvo.password_hash = hash_senha(body.password)

    db.commit()
    db.refresh(alvo)
    return {"ok": True, "user": _serialize(alvo)}


@router.delete("/{user_id}")
def remover(user_id: int, db: Session = Depends(get_db),
            ator: User = Depends(requer_papel("admin"))):
    alvo = db.get(User, user_id)
    if not alvo:
        raise HTTPException(404, "Usuário não encontrado")
    if alvo.role == "admin" and alvo.active and _admins_ativos(db) <= 1:
        raise HTTPException(400, "Não é possível excluir o último admin ativo")
    db.delete(alvo)
    db.commit()
    return {"ok": True, "id": user_id}
