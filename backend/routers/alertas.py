"""
backend/routers/alertas.py — Alertas do painel (protegidos por JWT).

GET  /alertas                      lista (100 mais recentes) + total_nao_lidos
POST /alertas/{id}/lido            marca um como lido
POST /alertas/marcar-todos-lidos   marca todos como lidos
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.deps import usuario_atual
from backend.models.alerta import Alerta

router = APIRouter(prefix="/alertas", tags=["alertas"], dependencies=[Depends(usuario_atual)])


def _serialize(a: Alerta) -> dict:
    return {
        "id": a.id, "ticker": a.ticker, "tipo": a.tipo, "mensagem": a.mensagem,
        "score": float(a.score) if a.score is not None else None,
        "sinal": a.sinal, "lido": bool(a.lido),
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


@router.get("")
def listar(db: Session = Depends(get_db)):
    alertas = db.query(Alerta).order_by(Alerta.created_at.desc()).limit(100).all()
    nao_lidos = (db.query(func.count(Alerta.id))
                   .filter(Alerta.lido.is_(False)).scalar()) or 0
    return {"alertas": [_serialize(a) for a in alertas], "total_nao_lidos": nao_lidos}


@router.post("/marcar-todos-lidos")
def marcar_todos_lidos(db: Session = Depends(get_db)):
    db.query(Alerta).filter(Alerta.lido.is_(False)).update({"lido": True})
    db.commit()
    return {"ok": True}


@router.post("/{alerta_id}/lido")
def marcar_lido(alerta_id: int, db: Session = Depends(get_db)):
    db.query(Alerta).filter(Alerta.id == alerta_id).update({"lido": True})
    db.commit()
    return {"ok": True}
