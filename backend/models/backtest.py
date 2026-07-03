"""backend/models/backtest.py — Cache de backtest (espelha backtest_runs)."""

from sqlalchemy import (
    Column, DateTime, Integer, Numeric, String, UniqueConstraint, func,
)

from backend.db import Base


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id           = Column(Integer, primary_key=True)
    ticker       = Column(String(10), nullable=False)
    periodo      = Column(String(10), nullable=False)   # período do request ("5y")
    retorno_pct  = Column(Numeric(8, 2))
    cagr_pct     = Column(Numeric(8, 2))
    sharpe       = Column(Numeric(6, 3))
    max_drawdown = Column(Numeric(8, 2))
    alpha_pct    = Column(Numeric(8, 2))
    win_rate_pct = Column(Numeric(6, 2))
    n_trades     = Column(Integer)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("ticker", "periodo", name="backtest_runs_ticker_periodo_key"),)
