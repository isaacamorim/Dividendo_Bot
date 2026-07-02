"""
data/market_data.py — Preços, médias móveis, momentum e beta via yfinance.

Exporta:
  get_preco_atual(ticker)              → float | None
  get_historico(ticker, period)        → DataFrame (vazio em caso de falha)
  get_dados_tecnicos_completos(ticker) → dict ({} em caso de falha)

Nunca levanta exceção — falhas de rede/dados retornam vazio e o chamador decide.
"""

import logging

import pandas as pd
import yfinance as yf

from config.settings import MA_CURTA, MA_LONGA

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

# Cache simples por execução (evita baixar o mesmo histórico 2x no mesmo scan)
_cache_hist = {}


def get_historico(ticker: str, period: str = "5y") -> pd.DataFrame:
    """Histórico de preços ajustados. DataFrame vazio se falhar."""
    chave = (ticker, period)
    if chave in _cache_hist:
        return _cache_hist[chave]
    try:
        df = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        if df is None:
            df = pd.DataFrame()
    except Exception:
        df = pd.DataFrame()
    _cache_hist[chave] = df
    return df


def get_preco_atual(ticker: str):
    """Último fechamento disponível. None se falhar."""
    df = get_historico(ticker, period="5d")
    if df.empty or "Close" not in df:
        return None
    return round(float(df["Close"].iloc[-1]), 2)


def get_dados_tecnicos_completos(ticker: str) -> dict:
    """
    MA50/MA200, tendência, momentum 12m/3m, suporte/resistência (90d),
    beta e eps_growth (via .info, quando disponíveis).
    """
    df = get_historico(ticker, period="2y")
    if df.empty or "Close" not in df or len(df) < 30:
        return {}

    close = df["Close"].squeeze()
    preco = float(close.iloc[-1])

    ma_c = float(close.rolling(MA_CURTA).mean().iloc[-1]) if len(close) >= MA_CURTA else None
    ma_l = float(close.rolling(MA_LONGA).mean().iloc[-1]) if len(close) >= MA_LONGA else None

    mom_12m = round((preco / float(close.iloc[-252]) - 1) * 100, 1) if len(close) >= 252 else None
    mom_3m  = round((preco / float(close.iloc[-63])  - 1) * 100, 1) if len(close) >= 63  else None

    janela_90d  = close.iloc[-90:]
    suporte     = round(float(janela_90d.min()), 2)
    resistencia = round(float(janela_90d.max()), 2)

    # beta e eps_growth vêm do .info — frequentemente ausentes p/ B3 (ver README).
    # Ausência NÃO penaliza: o score renormaliza os pesos.
    beta = eps_growth = None
    try:
        info = yf.Ticker(ticker).info or {}
        beta = info.get("beta")
        eg   = info.get("earningsGrowth")
        if eg is not None and abs(eg) < 10:          # sanity: descarta escala absurda
            eps_growth = round(eg * 100, 1)
    except Exception:
        pass

    return {
        "preco":          round(preco, 2),
        "ma_curta":       round(ma_c, 2) if ma_c is not None else None,
        "ma_longa":       round(ma_l, 2) if ma_l is not None else None,
        "tendencia_alta": (ma_c > ma_l) if (ma_c is not None and ma_l is not None) else None,
        "momentum_12m":   mom_12m,
        "momentum_3m":    mom_3m,
        "beta":           beta,
        "eps_growth":     eps_growth,
        "suporte":        suporte,
        "resistencia":    resistencia,
    }
