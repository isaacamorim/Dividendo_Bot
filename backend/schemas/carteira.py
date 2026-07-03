"""backend/schemas/carteira.py — Contratos da carteira (request/response)."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class PosicaoCreate(BaseModel):
    ticker: str
    preco_compra: float
    quantidade: int
    data_compra: date
    nota: Optional[str] = None


class DividendoCreate(BaseModel):
    ticker: str
    valor_por_acao: float
    data_pagamento: date


class PosicaoResponse(BaseModel):
    ticker: str
    qtd: int
    pm: float
    preco_atual: float
    investido: float
    atual: float
    lucro_cap: float
    rentabilidade_pct: float
    rent_total_pct: float
    dividendos: float


class CarteiraResumo(BaseModel):
    posicoes: List[PosicaoResponse]
    total_investido: float
    total_atual: float
    lucro_capital: float
    rentabilidade_pct: float
    total_dividendos: float
    rent_total_pct: float
    alertas: List[str] = []
