"""backend/models/watchlist.py — Watchlist gerenciável (espelha a tabela do 005)."""

from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String, Text, func,
)

from backend.db import Base


class Watchlist(Base):
    __tablename__ = "watchlist"

    id            = Column(Integer, primary_key=True)
    ticker        = Column(String(10), unique=True, nullable=False)
    nome          = Column(String(100))
    setor         = Column(String(50))
    setor_perfil  = Column(String(30))
    ativo         = Column(Boolean, default=True)
    adicionado_em = Column(DateTime(timezone=True), server_default=func.now())
    nota          = Column(Text)
