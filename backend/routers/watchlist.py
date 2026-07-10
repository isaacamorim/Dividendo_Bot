"""
backend/routers/watchlist.py — Gestão da watchlist pela UI (protegido por JWT).

GET    /watchlist              lista todos os ativos + perfis disponíveis
GET    /watchlist/validar/{tk} valida no yfinance e detecta setor (sem inserir)
POST   /watchlist              adiciona (valida + detecta setor)
PUT    /watchlist/{ticker}     atualiza setor_perfil / nota / ativo
DELETE /watchlist/{ticker}     soft delete (ativo = FALSE, preserva histórico)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.settings import PERFIS_SETOR, resolver_perfil

from backend.db import get_db
from backend.deps import EDITORES, requer_papel, usuario_atual
from backend.models.watchlist import Watchlist

router = APIRouter(prefix="/watchlist", tags=["watchlist"],
                   dependencies=[Depends(usuario_atual)])

# Leitor só lê a lista; validar/adicionar/editar/remover exige operador+.
_editor = Depends(requer_papel(*EDITORES))

# Labels de perfil p/ o dropdown do front (sem o "Geral" default).
_PERFIS_LABELS = sorted({p["label"] for k, p in PERFIS_SETOR.items() if k != "default"})


class WatchlistCreate(BaseModel):
    ticker: str
    setor_perfil: Optional[str] = None
    nota: Optional[str] = None


class WatchlistUpdate(BaseModel):
    setor_perfil: Optional[str] = None
    nota: Optional[str] = None
    ativo: Optional[bool] = None


def _limpo(t: str) -> str:
    return (t or "").upper().replace(".SA", "").strip()


def _serialize(w: Watchlist) -> dict:
    return {
        "ticker": w.ticker, "nome": w.nome, "setor": w.setor,
        "setor_perfil": w.setor_perfil, "ativo": bool(w.ativo),
        "adicionado_em": w.adicionado_em.isoformat() if w.adicionado_em else None,
        "nota": w.nota,
    }


def _validar_yf(tk: str) -> Optional[dict]:
    """Confere se o ticker existe na B3 e detecta nome/setor. None se não existe."""
    try:
        import yfinance as yf
        t = yf.Ticker(tk + ".SA")
        try:
            preco = t.fast_info.last_price
        except Exception:                           # noqa: BLE001
            preco = None
        if not preco:
            return None
        nome = setor_yf = None
        try:
            info = t.info or {}
            nome = info.get("longName") or info.get("shortName")
            setor_yf = info.get("sector")
        except Exception:                           # noqa: BLE001
            pass
        _, perfil = resolver_perfil(tk, setor_yf)
        return {"preco": round(float(preco), 2), "nome": nome,
                "setor_yf": setor_yf, "setor_perfil": perfil["label"]}
    except Exception:                               # noqa: BLE001
        return None


@router.get("")
def listar(db: Session = Depends(get_db)):
    ativos = db.query(Watchlist).order_by(Watchlist.setor_perfil, Watchlist.ticker).all()
    return {"ativos": [_serialize(w) for w in ativos], "total": len(ativos),
            "perfis": _PERFIS_LABELS}


@router.get("/validar/{ticker}", dependencies=[_editor])
def validar(ticker: str):
    tk = _limpo(ticker)
    if not tk:
        raise HTTPException(status_code=400, detail="Ticker vazio")
    info = _validar_yf(tk)
    if info is None:
        return {"valido": False, "ticker": tk}
    return {"valido": True, "ticker": tk, "nome": info["nome"],
            "setor": info["setor_yf"], "setor_perfil": info["setor_perfil"],
            "setor_detectado": info["setor_yf"] is not None}


@router.post("", dependencies=[_editor])
def adicionar(body: WatchlistCreate, db: Session = Depends(get_db)):
    tk = _limpo(body.ticker)
    if not tk:
        raise HTTPException(status_code=400, detail="Ticker vazio")
    info = _validar_yf(tk)
    if info is None:
        raise HTTPException(status_code=400, detail="Ticker não encontrado na B3")
    setor_perfil = body.setor_perfil or info["setor_perfil"]

    existente = db.query(Watchlist).filter(Watchlist.ticker == tk).first()
    if existente:
        # Ticker é UNIQUE: reativa/atualiza em vez de duplicar.
        existente.ativo = True
        existente.setor_perfil = setor_perfil
        existente.nome = existente.nome or info["nome"]
        existente.setor = existente.setor or info["setor_yf"]
        if body.nota is not None:
            existente.nota = body.nota
        db.commit()
        db.refresh(existente)
        return _serialize(existente)

    novo = Watchlist(ticker=tk, nome=info["nome"], setor=info["setor_yf"],
                     setor_perfil=setor_perfil, nota=body.nota, ativo=True)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return _serialize(novo)


@router.put("/{ticker}", dependencies=[_editor])
def atualizar(ticker: str, body: WatchlistUpdate, db: Session = Depends(get_db)):
    w = db.query(Watchlist).filter(Watchlist.ticker == _limpo(ticker)).first()
    if not w:
        raise HTTPException(status_code=404, detail="Ticker não está na watchlist")
    if body.setor_perfil is not None:
        w.setor_perfil = body.setor_perfil
    if body.nota is not None:
        w.nota = body.nota
    if body.ativo is not None:
        w.ativo = body.ativo
    db.commit()
    db.refresh(w)
    return _serialize(w)


@router.delete("/{ticker}", dependencies=[_editor])
def remover(ticker: str, db: Session = Depends(get_db)):
    w = db.query(Watchlist).filter(Watchlist.ticker == _limpo(ticker)).first()
    if not w:
        raise HTTPException(status_code=404, detail="Ticker não está na watchlist")
    w.ativo = False                                 # soft delete — preserva histórico
    db.commit()
    return {"ok": True, "ticker": w.ticker}
