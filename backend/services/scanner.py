"""
backend/services/scanner.py — Ponte entre a API e o core do scanner.

Reusa os blocos existentes (get_fundamentos, dados técnicos, analisar_ativo)
replicando o merge que o main.py faz em analisar(), mas SEM printing nem o
estado global DEMO_MODE do CLI. Roda sempre ao vivo.
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.dialects.postgresql import insert

from analysis.dividend_analysis import analisar_ativo
from config.settings import WATCHLIST_ACOES
from data.fundamentals import get_fundamentos
from data.market_data import get_dados_tecnicos_completos, get_preco_atual

from backend.models.snapshot import Snapshot

logger = logging.getLogger("dividend_bot.scanner")

_CAMPOS_UPSERT = (
    "preco", "ma200", "preco_justo", "upside", "dy", "roe", "pl",
    "score", "sinal", "estrategia", "setor_perfil", "div_estimado",
    "divida_ebitda", "payout", "eps_growth",
)


def _analisar_ticker(ticker_sa: str):
    fund = get_fundamentos(ticker_sa)
    tec = get_dados_tecnicos_completos(ticker_sa) or {}
    if not fund.get("preco"):
        fund["preco"] = get_preco_atual(ticker_sa)
    for campo in ("eps_growth", "beta", "momentum_12m", "momentum_3m"):
        if tec.get(campo) is not None and fund.get(campo) is None:
            fund[campo] = tec[campo]
    fund["ticker"] = ticker_sa.upper().replace(".SA", "")
    if fund.get("delisted"):
        return None
    return analisar_ativo(fund, tec)


def rodar_scan(watchlist: list | None = None) -> list:
    """Roda o scan ao vivo da watchlist. Nunca levanta — pula ticker que falhar."""
    tickers = watchlist or WATCHLIST_ACOES
    resultados = []
    for ticker in tickers:
        try:
            r = _analisar_ticker(ticker)
            if r:
                resultados.append(r)
        except Exception as e:                     # noqa: BLE001 — resiliência por ativo
            logger.warning("scan %s falhou: %s", ticker, e)
    return resultados


def _linha_snapshot(r: dict, dia: date) -> dict:
    f = r.get("fundamentos", {}) or {}
    v = r.get("valuation", {}) or {}
    t = r.get("tecnico", {}) or {}
    return {
        "ticker": r["ticker"], "data": dia,
        "preco": f.get("preco"), "ma200": t.get("ma_longa"),
        "preco_justo": v.get("preco_justo"),
        "upside": v.get("upside"), "dy": f.get("dy"), "roe": f.get("roe"),
        "pl": f.get("pl"), "score": r.get("score"), "sinal": r.get("sinal"),
        "estrategia": r.get("estrategia"), "setor_perfil": r.get("setor_perfil"),
        "div_estimado": v.get("div_estimado"),
        "divida_ebitda": f.get("divida_ebitda"), "payout": f.get("payout"),
        "eps_growth": f.get("eps_growth"),
    }


def salvar_snapshots(db, resultados: list, dia: date | None = None) -> int:
    """Upsert de um snapshot por ticker/dia (UNIQUE ticker,data). Retorna nº de linhas."""
    dia = dia or date.today()
    linhas = [_linha_snapshot(r, dia) for r in resultados]
    if not linhas:
        return 0
    stmt = insert(Snapshot).values(linhas)
    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker", "data"],
        set_={c: getattr(stmt.excluded, c) for c in _CAMPOS_UPSERT},
    )
    db.execute(stmt)
    db.commit()
    return len(linhas)
