"""
backend/routers/backtest.py — Backtest via API com cache no banco (JWT).

GET /backtest/comparativo?periodo=5y   ranking da watchlist + alpha médio
GET /backtest/{ticker}?periodo=5y      resultado (cache < 24h, senão roda)

Ordem importa: /comparativo é declarado ANTES de /{ticker} para não ser
capturado como ticker="comparativo".
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backtest.backtester_fundamental import backtest_fundamental

from backend.db import get_db
from backend.deps import usuario_atual
from backend.models.snapshot import Snapshot
from backend.services.backtest_service import backtest_comparativo, backtest_ticker

router = APIRouter(prefix="/backtest", tags=["backtest"], dependencies=[Depends(usuario_atual)])


def _f(x):
    return float(x) if x is not None else None


@router.get("/comparativo")
def comparativo(periodo: str = Query("5y"), db: Session = Depends(get_db)):
    return backtest_comparativo(db, periodo)


@router.get("/fundamental/{ticker}")
def backtest_fund(ticker: str, db: Session = Depends(get_db)):
    """Backtest fundamental sobre a série de snapshots do banco (sem cache)."""
    tk = ticker.upper().replace(".SA", "")
    rows = db.query(Snapshot).filter(Snapshot.ticker == tk).order_by(Snapshot.data).all()
    snaps = [{"data": r.data.isoformat(), "preco": _f(r.preco),
              "score": _f(r.score), "roe": _f(r.roe)} for r in rows]
    return backtest_fundamental(snaps, tk)


@router.get("/{ticker}")
def backtest(ticker: str, periodo: str = Query("5y"), db: Session = Depends(get_db)):
    return backtest_ticker(db, ticker, periodo)
