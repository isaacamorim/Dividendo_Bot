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

import pandas as pd
import yfinance as yf

from data.cache import TTL_FUNDAMENTOS_H, cache

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


def get_fundamentos(ticker: str, usar_cache: bool = True) -> dict:
    """Coleta e normaliza fundamentos. Nunca levanta exceção.

    Checa o cache local antes de bater no yfinance; só grava no cache
    resultados válidos (com preço), pra não persistir falha transitória.
    """
    t_limpo = ticker.upper().replace(".SA", "")

    if usar_cache:
        em_cache = cache.get(t_limpo)
        if em_cache is not None:
            return em_cache

    base = {
        "ticker": t_limpo, "nome": None, "setor": None, "preco": None,
        "dy": None, "roe": None, "pl": None, "lpa": None, "pvp": None,
        "payout": None, "divida_ebitda": None, "eps_growth": None,
        "beta": None, "delisted": False,
    }

    try:
        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info or {}
    except Exception:
        yf_ticker = None
        info = {}

    preco = (info.get("currentPrice") or info.get("regularMarketPrice")
             or info.get("previousClose"))
    if not preco:
        base["delisted"] = True
        return base

    base["preco"] = round(float(preco), 2)
    base["nome"]  = info.get("shortName") or info.get("longName")
    base["setor"] = info.get("sector")

    # ── DY: série real de proventos dos últimos 12 meses ÷ preço ─────────────
    # Fonte de verdade > campo trailingAnnualDividendRate (que ora subreporta,
    # ora tem escala inconsistente). Ancorado em HOJE (TTM), não no último
    # pagamento — calendário irregular ancorado no último provento superconta
    # (BBAS3: .last daria 4,9% vs 2,7% real por incluir provento de 13 meses).
    dy_serie = None
    if yf_ticker is not None and preco:
        try:
            divs = yf_ticker.dividends
            if divs is not None and not divs.empty:
                corte = pd.Timestamp.now(tz=divs.index.tz) - pd.DateOffset(years=1)
                soma_12m = float(divs[divs.index >= corte].sum())
                dy_serie = round(soma_12m / float(preco) * 100, 1)
        except Exception:
            dy_serie = None

    if dy_serie is not None and 0 <= dy_serie <= 40:      # >40% = lixo/evento único
        base["dy"] = dy_serie
    else:
        # Fallback: campo do info (série vazia, preço 0, ou fora do sanity)
        div_rate = info.get("trailingAnnualDividendRate") or info.get("dividendRate")
        if div_rate and preco:
            dy = round(float(div_rate) / float(preco) * 100, 1)
            base["dy"] = dy if 0 <= dy <= 40 else None
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

    if usar_cache:
        cache.set(t_limpo, base, TTL_FUNDAMENTOS_H)

    return base
