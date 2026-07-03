"""
backend/services/carteira_service.py — Resumo da carteira reusando o core.

Em vez de duplicar a matemática (PM, rentabilidade, rent_total), monta a
estrutura interna que portfolio.carteira.Carteira espera a partir das linhas
do banco e chama Carteira.resumo() — a MESMA lógica do CLI. Preços atuais vêm
de get_preco_atual() do core (não inventa fetcher novo).
"""

from __future__ import annotations

import os

from data.market_data import get_preco_atual
from portfolio.carteira import Carteira

from backend.models.carteira import DividendoRecebido, Posicao

# Caminho inexistente de propósito: Carteira só lê no __init__ (vira vazio) e
# nós sobrescrevemos _dados. resumo()/posicoes() não gravam nada.
_ARQ_NULO = os.path.join(os.path.dirname(__file__), "__carteira_none__.json")


def _carteira_do_banco(db) -> Carteira:
    c = Carteira(arquivo=_ARQ_NULO)
    dados = {"posicoes": {}, "dividendos": [], "historico": []}
    for p in db.query(Posicao).order_by(Posicao.data_compra).all():
        d = dados["posicoes"].setdefault(p.ticker, {"lotes": [], "dividendos_recebidos": 0.0})
        d["lotes"].append({
            "data": p.data_compra.isoformat(),
            "preco": float(p.preco_compra),
            "qtd": p.quantidade,
            "nota": p.nota or "",
        })
    for dv in db.query(DividendoRecebido).all():
        d = dados["posicoes"].setdefault(dv.ticker, {"lotes": [], "dividendos_recebidos": 0.0})
        d["dividendos_recebidos"] = round(d["dividendos_recebidos"] + float(dv.total), 2)
    c._dados = dados
    return c


def resumo_carteira(db) -> dict:
    c = _carteira_do_banco(db)

    precos = {}
    for p in c.posicoes():
        try:
            precos[p["ticker"]] = get_preco_atual(p["ticker"] + ".SA")
        except Exception:
            precos[p["ticker"]] = None

    r = c.resumo(precos)
    # Renomeia as chaves de posição para o contrato da API (schema).
    r["posicoes"] = [
        {
            "ticker": p["ticker"], "qtd": p["qtd"], "pm": p["pm"],
            "preco_atual": p["preco_atual"], "investido": p["investido"],
            "atual": p["atual"], "lucro_cap": p["lucro_cap"],
            "rentabilidade_pct": p["rent_pct"], "rent_total_pct": p["rent_total"],
            "dividendos": p["dividendos"],
        }
        for p in r["posicoes"]
    ]
    r.setdefault("lucro_capital", round(r["total_atual"] - r["total_investido"], 2))
    r["alertas"] = c.alertas_risco()
    return r
