"""backend/models/snapshot.py — Snapshot diário de um ativo (espelha a tabela snapshots)."""

from sqlalchemy import (
    Column, Date, DateTime, Integer, Numeric, String, UniqueConstraint, func,
)

from backend.db import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    id           = Column(Integer, primary_key=True)
    ticker       = Column(String(10), nullable=False)
    data         = Column(Date, nullable=False)
    preco        = Column(Numeric(10, 2))
    ma200        = Column(Numeric(10, 2))
    preco_justo  = Column(Numeric(10, 2))
    upside       = Column(Numeric(6, 2))
    dy           = Column(Numeric(6, 2))
    roe          = Column(Numeric(6, 2))
    pl           = Column(Numeric(8, 2))
    score        = Column(Numeric(4, 2))
    sinal        = Column(String(10))
    estrategia   = Column(String(15))
    setor_perfil = Column(String(30))
    div_estimado = Column(Numeric(8, 2))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("ticker", "data", name="snapshots_ticker_data_key"),)
