"""backend/schemas/backtest.py — Contratos do backtest."""

from typing import Any, List, Optional

from pydantic import BaseModel


class BacktestRequest(BaseModel):
    ticker: str
    periodo: str = "5y"


class BacktestResponse(BaseModel):
    ticker: str
    periodo: str
    origem: str                       # "cache" ou "fresh"
    retorno_pct: Optional[float] = None
    cagr_pct: Optional[float] = None
    sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    alpha_pct: Optional[float] = None
    win_rate_pct: Optional[float] = None
    n_trades: Optional[int] = None
    trades: List[Any] = []
