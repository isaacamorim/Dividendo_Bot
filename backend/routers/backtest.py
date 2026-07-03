"""
backend/routers/backtest.py — Backtest via API com cache no banco (JWT).

GET /backtest/comparativo?periodo=5y   ranking da watchlist + alpha médio
GET /backtest/{ticker}?periodo=5y      resultado (cache < 24h, senão roda)

Ordem importa: /comparativo é declarado ANTES de /{ticker} para não ser
capturado como ticker="comparativo".
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.deps import usuario_atual
from backend.services.backtest_service import backtest_comparativo, backtest_ticker

router = APIRouter(prefix="/backtest", tags=["backtest"], dependencies=[Depends(usuario_atual)])


@router.get("/comparativo")
def comparativo(periodo: str = Query("5y"), db: Session = Depends(get_db)):
    return backtest_comparativo(db, periodo)


@router.get("/{ticker}")
def backtest(ticker: str, periodo: str = Query("5y"), db: Session = Depends(get_db)):
    return backtest_ticker(db, ticker, periodo)
