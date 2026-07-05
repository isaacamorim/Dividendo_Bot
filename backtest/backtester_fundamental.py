"""
backtest/backtester_fundamental.py — Backtest da TESE DE DIVIDENDOS (não swing).

Estratégia híbrida (Opção C), operando sobre a série de SNAPSHOTS do banco
(score/roe/preço por dia) — NÃO usa yfinance:

  ENTRADA: score >= score_entrada.
  SAÍDA (qualquer uma):
    1. score < score_saida por 'periodos_saida' snapshots consecutivos
       (deterioração sustentada, não ruído);
    2. ROE caiu > 30% vs. o do dia da compra;
    3. dívida/EBITDA > divida_max_setor × 1.8 E score < 6.0 (só avaliada se a
       série trouxer divida_ebitda — snapshots antigos não têm; None = ignora).

O core é desacoplado do banco: esta função recebe a série pronta. O endpoint
da API busca os snapshots e chama aqui.
"""

from __future__ import annotations

from datetime import date, datetime

from config.settings import resolver_perfil

CAPITAL_INICIAL = 10_000.0


def _to_date(d):
    if isinstance(d, date):
        return d
    return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()


def _max_drawdown(hist: list) -> float:
    if not hist:
        return 0.0
    peak = hist[0]
    mdd = 0.0
    for v in hist:
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100 if peak else 0.0
        if dd < mdd:
            mdd = dd
    return round(mdd, 2)


def backtest_fundamental(snapshots: list, ticker: str = "",
                         score_entrada: float = 7.0, score_saida: float = 5.0,
                         periodos_saida: int = 3) -> dict:
    """Simula compra/venda por fundamentos sobre a série de snapshots (ordem ASC)."""
    n = len(snapshots)
    nota = "⚠️ Poucos dados históricos — resultado indicativo" if n < 30 else None

    base = {"ticker": ticker, "retorno_pct": 0.0, "cagr_pct": 0.0, "n_trades": 0,
            "win_rate_pct": 0.0, "max_drawdown": 0.0, "periodo": "",
            "trades": [], "nota_dados": nota}
    if n == 0:
        return base

    limite = resolver_perfil(ticker)[1].get("divida_max") if ticker else None

    capital = CAPITAL_INICIAL
    qtd = 0
    pos = None            # {"data", "preco", "roe"}
    dias_abaixo = 0
    trades = []
    capital_hist = []

    for s in snapshots:
        preco = s.get("preco")
        score = s.get("score")
        roe = s.get("roe")
        data = s.get("data")
        if preco is None or score is None:
            continue

        if pos is None:
            if score >= score_entrada:
                qtd = int(capital // preco)
                if qtd > 0:
                    capital -= qtd * preco
                    pos = {"data": data, "preco": preco, "roe": roe}
                    dias_abaixo = 0
                    trades.append({"tipo": "COMPRA", "data": data,
                                   "preco": round(preco, 2), "qtd": qtd})
        else:
            dias_abaixo = dias_abaixo + 1 if score < score_saida else 0
            motivo = None
            if dias_abaixo >= periodos_saida:
                motivo = f"score < {score_saida:g} por {periodos_saida} dias"
            elif (pos["roe"] is not None and pos["roe"] > 0
                  and roe is not None and roe < pos["roe"] * 0.70):
                motivo = f"ROE caiu >30% ({pos['roe']:.0f}%->{roe:.0f}%)"
            elif (limite and s.get("divida_ebitda") is not None
                  and s["divida_ebitda"] > limite * 1.8 and score < 6.0):
                motivo = "alavancagem explodiu + qualidade caindo"

            if motivo:
                capital += qtd * preco
                lucro = qtd * (preco - pos["preco"])
                trades.append({"tipo": "VENDA", "data": data, "preco": round(preco, 2),
                               "qtd": qtd, "lucro": round(lucro, 2), "motivo": motivo})
                pos = None
                qtd = 0
                dias_abaixo = 0

        capital_hist.append(round(capital + qtd * preco, 2))

    # Fecha posição aberta no último snapshot.
    if pos is not None:
        ult = snapshots[-1]
        preco_fim = ult.get("preco") or pos["preco"]
        capital += qtd * preco_fim
        lucro = qtd * (preco_fim - pos["preco"])
        trades.append({"tipo": "VENDA", "data": ult.get("data"), "preco": round(preco_fim, 2),
                       "qtd": qtd, "lucro": round(lucro, 2), "motivo": "fim do período"})

    ret_total = (capital / CAPITAL_INICIAL - 1) * 100
    d0, d1 = _to_date(snapshots[0]["data"]), _to_date(snapshots[-1]["data"])
    anos = max((d1 - d0).days / 365.25, 1e-9)
    cagr = ((1 + ret_total / 100) ** (1 / anos) - 1) * 100
    vendas = [t for t in trades if t["tipo"] == "VENDA"]
    wins = sum(1 for t in vendas if t["lucro"] > 0)

    return {
        "ticker": ticker,
        "retorno_pct": round(ret_total, 2),
        "cagr_pct": round(cagr, 2),
        "n_trades": sum(1 for t in trades if t["tipo"] == "COMPRA"),
        "win_rate_pct": round(wins / len(vendas) * 100, 1) if vendas else 0.0,
        "max_drawdown": _max_drawdown(capital_hist),
        "periodo": f"{d0.isoformat()} -> {d1.isoformat()}",
        "trades": trades,
        "nota_dados": nota,
    }
