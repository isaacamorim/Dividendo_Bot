"""
backend/services/backtest_service.py — Backtest com cache no banco.

Reusa rodar_backtest() do core. Cache por (ticker, periodo): se houver run
com < 24h, devolve o resumo do banco (rápido); senão roda ao vivo, salva o
resumo (upsert) e devolve o resultado completo (com trades).

A tabela backtest_runs guarda só métricas-resumo (schema do PRD) — trades e
histórico de capital só vêm no run fresh.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from backtest.backtester import rodar_backtest
from config.settings import WATCHLIST_ACOES, resolver_perfil

from backend.models.backtest import BacktestRun

_CACHE_HORAS = 24

_METRICAS = ("retorno_pct", "cagr_pct", "sharpe", "max_drawdown",
             "alpha_pct", "win_rate_pct", "n_trades")

# Teto por coluna Numeric(p, s): |valor| < 10^(p-s). Blindagem para um valor
# patologico (nan/inf/degenerado) nunca estourar o INSERT e derrubar o
# endpoint comparativo, que itera toda a watchlist.
_LIMITES = {
    "retorno_pct": 1e6, "cagr_pct": 1e6, "max_drawdown": 1e6,
    "alpha_pct": 1e6, "win_rate_pct": 1e4, "sharpe": 1e3,
}


def _sanear(metrica: str, valor):
    """Garante que a metrica cabe na coluna: nan/inf -> None; clamp ao teto."""
    if valor is None or metrica == "n_trades":
        return valor
    try:
        f = float(valor)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    lim = _LIMITES.get(metrica)
    if lim is not None:
        teto = lim - 0.01
        f = max(-teto, min(teto, f))
    return f


def _limpo(ticker: str) -> str:
    return ticker.upper().replace(".SA", "")


def _cache_valido(run: BacktestRun | None) -> bool:
    if run is None or run.created_at is None:
        return False
    return datetime.now(timezone.utc) - run.created_at < timedelta(hours=_CACHE_HORAS)


def _num(x):
    return float(x) if x is not None else None


def _run_para_dict(run: BacktestRun) -> dict:
    return {
        "ticker": run.ticker, "periodo": run.periodo, "origem": "cache",
        "retorno_pct": _num(run.retorno_pct), "cagr_pct": _num(run.cagr_pct),
        "sharpe": _num(run.sharpe), "max_drawdown": _num(run.max_drawdown),
        "alpha_pct": _num(run.alpha_pct), "win_rate_pct": _num(run.win_rate_pct),
        "n_trades": run.n_trades, "trades": [],
        "created_at": run.created_at.isoformat(),
    }


def _salvar(db, ticker: str, periodo: str, res: dict):
    valores = {"ticker": ticker, "periodo": periodo, "created_at": func.now()}
    valores.update({m: _sanear(m, res.get(m)) for m in _METRICAS})
    stmt = insert(BacktestRun).values(**valores)
    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker", "periodo"],
        set_={**{m: getattr(stmt.excluded, m) for m in _METRICAS},
              "created_at": func.now()},
    )
    db.execute(stmt)
    db.commit()


def backtest_ticker(db, ticker: str, periodo: str = "5y") -> dict:
    tk = _limpo(ticker)
    run = db.query(BacktestRun).filter_by(ticker=tk, periodo=periodo).first()
    if _cache_valido(run):
        return _run_para_dict(run)

    res = rodar_backtest(tk + ".SA", period=periodo)
    if "erro" in res:
        return {"ticker": tk, "periodo": periodo, "origem": "fresh", "erro": res["erro"]}

    _salvar(db, tk, periodo, res)
    saida = dict(res)
    saida["ticker"] = tk
    saida["intervalo_datas"] = res.get("periodo")   # o "periodo" do core é intervalo de datas
    saida["periodo"] = periodo                       # o nosso periodo é o do request
    saida["origem"] = "fresh"
    return saida


def backtest_comparativo(db, periodo: str = "5y") -> dict:
    resultados = []
    for ticker in WATCHLIST_ACOES:
        r = backtest_ticker(db, ticker, periodo)
        if "erro" not in r:
            resultados.append(r)

    if not resultados:
        return {"periodo": periodo, "resultados": [], "alpha_medio": None, "pct_venceu_bh": None}

    ranking = sorted(resultados, key=lambda x: -(x.get("retorno_pct") or -9999))
    alphas = [x["alpha_pct"] for x in resultados if x.get("alpha_pct") is not None]
    alpha_medio = round(sum(alphas) / len(alphas), 2) if alphas else None
    pct_venceu = round(sum(1 for a in alphas if a > 0) / len(alphas) * 100, 1) if alphas else None
    pct_lucro = round(sum(1 for x in resultados if (x.get("retorno_pct") or 0) > 0)
                      / len(resultados) * 100, 1)

    return {
        "periodo": periodo,
        "n_ativos": len(resultados),
        "alpha_medio": alpha_medio,
        "pct_venceu_bh": pct_venceu,
        "pct_com_lucro": pct_lucro,
        "ranking": [
            {"ticker": x["ticker"], "setor": resolver_perfil(x["ticker"])[1]["label"],
             "retorno_pct": x.get("retorno_pct"), "cagr_pct": x.get("cagr_pct"),
             "alpha_pct": x.get("alpha_pct"), "sharpe": x.get("sharpe"),
             "win_rate_pct": x.get("win_rate_pct"), "n_trades": x.get("n_trades"),
             "origem": x.get("origem")}
            for x in ranking
        ],
    }
