"""backend/models/carteira.py — Posições e dividendos recebidos (espelham as tabelas do 001_init.sql)."""

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, Text, func

from backend.db import Base


class Posicao(Base):
    __tablename__ = "posicoes"

    id           = Column(Integer, primary_key=True)
    ticker       = Column(String(10), nullable=False)
    data_compra  = Column(Date, nullable=False)
    preco_compra = Column(Numeric(10, 2), nullable=False)
    quantidade   = Column(Integer, nullable=False)
    nota         = Column(Text)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


class DividendoRecebido(Base):
    __tablename__ = "dividendos_recebidos"

    id             = Column(Integer, primary_key=True)
    ticker         = Column(String(10), nullable=False)
    data_pagamento = Column(Date, nullable=False)
    valor_por_acao = Column(Numeric(8, 4), nullable=False)
    quantidade     = Column(Integer, nullable=False)
    total          = Column(Numeric(10, 2), nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
