"""backend/models/alerta.py — Alertas do painel (espelha a tabela alertas do 004)."""

from sqlalchemy import (
    Boolean, Column, DateTime, Integer, Numeric, String, Text, func,
)

from backend.db import Base


class Alerta(Base):
    __tablename__ = "alertas"

    id         = Column(Integer, primary_key=True)
    ticker     = Column(String(10), nullable=False)
    tipo       = Column(String(30), nullable=False)   # NOVO_BUY|SAIU_BUY|STOP_LOSS|TAKE_PROFIT
    mensagem   = Column(Text, nullable=False)
    score      = Column(Numeric(4, 2))
    sinal      = Column(String(10))
    lido       = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
