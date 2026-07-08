"""
backend/routers/scan.py — Endpoints de scan (protegidos por JWT).

GET  /scan/latest            último snapshot de cada ativo (roda ao vivo se não houver de hoje)
POST /scan/run               força scan ao vivo agora e salva
GET  /scan/historico/{tk}    série de score/sinal/preço/upside nos últimos N dias
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.deps import usuario_atual
from backend.models.snapshot import Snapshot
from backend.services.scanner import rodar_scan, salvar_snapshots

router = APIRouter(prefix="/scan", tags=["scan"], dependencies=[Depends(usuario_atual)])


def _f(x):
    return float(x) if x is not None else None


def _serialize(s: Snapshot) -> dict:
    return {
        "ticker": s.ticker, "data": s.data.isoformat(),
        "preco": _f(s.preco), "ma200": _f(s.ma200),
        "preco_justo": _f(s.preco_justo), "upside": _f(s.upside),
        "dy": _f(s.dy), "roe": _f(s.roe), "pl": _f(s.pl), "score": _f(s.score),
        "sinal": s.sinal, "estrategia": s.estrategia, "setor_perfil": s.setor_perfil,
        "div_estimado": _f(s.div_estimado),
        "divida_ebitda": _f(s.divida_ebitda), "payout": _f(s.payout),
        "eps_growth": _f(s.eps_growth),
        "frequencia": "mensal" if s.setor_perfil == "FII" else "anual",
    }


def _ultimos_por_ticker(db: Session):
    sub = (db.query(Snapshot.ticker, func.max(Snapshot.data).label("md"))
             .group_by(Snapshot.ticker).subquery())
    return (db.query(Snapshot)
              .join(sub, (Snapshot.ticker == sub.c.ticker) & (Snapshot.data == sub.c.md))
              .all())


def _top5(rows):
    ordenados = sorted(rows, key=lambda s: -(float(s.score) if s.score is not None else -1))
    return [_serialize(s) for s in ordenados[:5]]


@router.get("/latest")
def latest(db: Session = Depends(get_db)):
    hoje = date.today()
    if not db.query(Snapshot).filter(Snapshot.data == hoje).first():
        salvar_snapshots(db, rodar_scan(), hoje)
    rows = _ultimos_por_ticker(db)
    return {"data": hoje.isoformat(),
            "resultados": [_serialize(s) for s in rows],
            "top5": _top5(rows)}


@router.post("/run")
def run(db: Session = Depends(get_db)):
    n = salvar_snapshots(db, rodar_scan(), date.today())
    rows = db.query(Snapshot).filter(Snapshot.data == date.today()).all()
    return {"status": "ok", "salvos": n, "resultados": [_serialize(s) for s in rows]}


@router.get("/analisar-gpt/{ticker}")
def analisar_gpt(ticker: str, db: Session = Depends(get_db)):
    """Parecer qualitativo do GPT sobre o ativo (snapshot + fundamentos ao vivo)."""
    tk = ticker.upper().replace(".SA", "")
    snap = (db.query(Snapshot).filter(Snapshot.ticker == tk)
              .order_by(Snapshot.data.desc()).first())
    if not snap:
        return {"disponivel": False}

    # P/VP e beta não ficam no snapshot — vêm dos fundamentos (best-effort).
    fund = {}
    try:
        from data.fundamentals import get_fundamentos
        fund = get_fundamentos(tk + ".SA") or {}
    except Exception:                               # noqa: BLE001
        fund = {}

    preco = _f(snap.preco)
    ma200 = _f(snap.ma200)
    tendencia = None
    if preco is not None and ma200 is not None:
        tendencia = "ALTA" if preco >= ma200 else "BAIXA"

    resultado = {
        "ticker": tk, "setor_perfil": snap.setor_perfil, "estrategia": snap.estrategia,
        "score": _f(snap.score), "sinal": snap.sinal,
        "fundamentos": {
            "dy": _f(snap.dy), "roe": _f(snap.roe), "pl": _f(snap.pl),
            "pvp": fund.get("pvp"), "payout": _f(snap.payout),
            "divida_ebitda": _f(snap.divida_ebitda), "eps_growth": _f(snap.eps_growth),
            "beta": fund.get("beta"), "preco": preco,
        },
        "valuation": {
            "preco_justo": _f(snap.preco_justo), "upside": _f(snap.upside),
            "div_estimado": _f(snap.div_estimado),
        },
        "tecnico": {
            "ma_longa": ma200, "momentum_12m": fund.get("momentum_12m"),
            "tendencia": tendencia,
        },
    }

    from backend.services.gpt_analyst import analisar_ativo_gpt
    analise = analisar_ativo_gpt(resultado)
    if analise is None:
        return {"disponivel": False}
    return {"disponivel": True, "ticker": tk, "analise": analise}


@router.get("/historico/{ticker}")
def historico(ticker: str, dias: int = Query(30, ge=1, le=3650),
              db: Session = Depends(get_db)):
    tk = ticker.upper().replace(".SA", "")
    limite = date.today() - timedelta(days=dias)
    rows = (db.query(Snapshot)
              .filter(Snapshot.ticker == tk, Snapshot.data >= limite)
              .order_by(Snapshot.data).all())
    serie = [{"data": s.data.isoformat(), "score": _f(s.score), "sinal": s.sinal,
              "preco": _f(s.preco), "preco_justo": _f(s.preco_justo),
              "upside": _f(s.upside), "dy": _f(s.dy), "roe": _f(s.roe),
              "divida_ebitda": _f(s.divida_ebitda), "payout": _f(s.payout),
              "eps_growth": _f(s.eps_growth)}
             for s in rows]
    return {"ticker": tk, "serie": serie}
