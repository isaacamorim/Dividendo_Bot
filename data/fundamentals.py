"""
data/fundamentals.py — Fundamentos via yfinance, com sanity checks de escala.

Contrato (dict retornado por get_fundamentos):
  ticker, nome, setor, preco, dy, roe, pl, lpa, pvp, payout,
  divida_ebitda, eps_growth, beta, delisted

Unidades: dy/roe/payout/eps_growth em PONTOS PERCENTUAIS (6.5 = 6,5%).
Yahoo é inconsistente p/ B3 (DY ora fração, ora %; LPA ausente etc.) —
este módulo normaliza e, na dúvida, devolve None (o score renormaliza).
"""

import logging

import yfinance as yf

logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def _pct_norm(valor, limite_pct: float):
    """
    Normaliza métrica percentual do Yahoo: fração (0.065) → 6.5.
    Valores fora de ±limite_pct são considerados lixo → None.
    """
    if valor is None:
        return None
    v = float(valor)
    if abs(v) <= 1.0:            # veio como fração
        v *= 100
    if abs(v) > limite_pct:      # escala absurda mesmo após normalizar
        return None
    return round(v, 1)


def get_fundamentos(ticker: str) -> dict:
    """Coleta e normaliza fundamentos. Nunca levanta exceção."""
    t_limpo = ticker.upper().replace(".SA", "")
    base = {
        "ticker": t_limpo, "nome": None, "setor": None, "preco": None,
        "dy": None, "roe": None, "pl": None, "lpa": None, "pvp": None,
        "payout": None, "divida_ebitda": None, "eps_growth": None,
        "beta": None, "delisted": False,
    }

    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        info = {}

    preco = (info.get("currentPrice") or info.get("regularMarketPrice")
             or info.get("previousClose"))
    if not preco:
        base["delisted"] = True
        return base

    base["preco"] = round(float(preco), 2)
    base["nome"]  = info.get("shortName") or info.get("longName")
    base["setor"] = info.get("sector")

    # ── DY: rota primária à prova de escala — dividendos/ação ÷ preço ────────
    div_rate = info.get("trailingAnnualDividendRate") or info.get("dividendRate")
    if div_rate and preco:
        dy = round(float(div_rate) / float(preco) * 100, 1)
        base["dy"] = dy if 0 <= dy <= 40 else None      # >40% = lixo/evento único
    else:
        base["dy"] = _pct_norm(info.get("dividendYield"), 40)

    # ── Rentabilidade e múltiplos ─────────────────────────────────────────────
    base["roe"] = _pct_norm(info.get("returnOnEquity"), 200)

    pl = info.get("trailingPE")
    if pl is not None and 0 < float(pl) <= 200:
        base["pl"] = round(float(pl), 1)

    lpa = info.get("trailingEps")
    if lpa is not None:
        base["lpa"] = round(float(lpa), 2)               # negativo é informação, mantém

    pvp = info.get("priceToBook")
    if pvp is not None and 0 < float(pvp) <= 50:
        base["pvp"] = round(float(pvp), 2)

    base["payout"] = _pct_norm(info.get("payoutRatio"), 300)

    # ── Dívida/EBITDA (bancos não têm EBITDA → None, e tudo bem) ─────────────
    total_debt = info.get("totalDebt")
    ebitda     = info.get("ebitda")
    if total_debt and ebitda and float(ebitda) > 0:
        de = float(total_debt) / float(ebitda)
        base["divida_ebitda"] = round(de, 1) if de <= 20 else None

    # ── Crescimento e risco ───────────────────────────────────────────────────
    eg = info.get("earningsGrowth")
    if eg is not None and abs(float(eg)) < 10:
        base["eps_growth"] = round(float(eg) * 100, 1)

    beta = info.get("beta")
    if beta is not None and 0 < float(beta) < 5:
        base["beta"] = round(float(beta), 2)

    return base
