"""
data/demo_data.py — Dados simulados para uso offline (--demo).

Calibrado com o gabarito real de 10/03/2026 (reports/relatorio_20260310_1724.html):
preço, MA200, DY, ROE, P/L e payout são os valores reais daquele scan.
PVP, dívida, EPS growth e beta foram estimados para reproduzir os mesmos
scores e sinais do gabarito (2 BUY: PETR4 e BBAS3 · 0 SELL · 10 HOLD).
"""

# ─────────────────────────────────────────────────────────────────────────────
#  Base de dados demo (ordenada por score do gabarito)
#  dy/roe/payout em pontos percentuais · divida_ebitda None = não se aplica
# ─────────────────────────────────────────────────────────────────────────────

DEMO_ACOES = {
    "WEGE3":  dict(nome="WEG S.A.",                 setor="Industrial/Growth",
                   preco=48.20, dy=1.8,  roe=35.4, pl=30.7, pvp=9.0,  payout=32,
                   divida_ebitda=0.2,  eps_growth=18.0,  beta=0.85,
                   ma_curta=46.80, ma_longa=45.00, momentum_12m=14.0, momentum_3m=4.5),
    "PETR4":  dict(nome="Petróleo Brasileiro S.A.", setor="Petróleo/Gás",
                   preco=37.80, dy=11.8, roe=24.6, pl=4.1,  pvp=1.1,  payout=38,
                   divida_ebitda=0.9,  eps_growth=4.0,   beta=1.40,
                   ma_curta=37.10, ma_longa=36.50, momentum_12m=9.0,  momentum_3m=3.2),
    "ITUB4":  dict(nome="Itaú Unibanco Holding",    setor="Bancos/Fin.",
                   preco=34.80, dy=7.5,  roe=21.1, pl=10.8, pvp=1.9,  payout=55,
                   divida_ebitda=None, eps_growth=6.0,   beta=0.95,
                   ma_curta=33.90, ma_longa=32.80, momentum_12m=11.0, momentum_3m=2.8),
    "TAEE11": dict(nome="Transmissora Aliança E.",  setor="Energia",
                   preco=33.20, dy=8.5,  roe=23.4, pl=28.1, pvp=1.1,  payout=61,
                   divida_ebitda=3.5,  eps_growth=0.0,   beta=0.70,
                   ma_curta=32.40, ma_longa=31.00, momentum_12m=7.5,  momentum_3m=2.0),
    "BBAS3":  dict(nome="Banco do Brasil S.A.",     setor="Bancos/Fin.",
                   preco=28.40, dy=9.1,  roe=19.2, pl=5.2,  pvp=0.9,  payout=42,
                   divida_ebitda=None, eps_growth=2.0,   beta=1.00,
                   ma_curta=27.20, ma_longa=25.50, momentum_12m=12.5, momentum_3m=5.1),
    "VALE3":  dict(nome="Vale S.A.",                setor="Commodities",
                   preco=62.30, dy=6.1,  roe=18.7, pl=6.4,  pvp=1.2,  payout=35,
                   divida_ebitda=0.7,  eps_growth=-15.0, beta=1.45,
                   # MA50 abaixo da MA200 → tendência de baixa (por isso HOLD no gabarito)
                   ma_curta=59.80, ma_longa=60.20, momentum_12m=-4.0, momentum_3m=-2.5),
    "EGIE3":  dict(nome="Engie Brasil Energia S.A.", setor="Energia",
                   preco=41.60, dy=7.2,  roe=31.5, pl=21.4, pvp=3.0,  payout=66,
                   divida_ebitda=2.8,  eps_growth=5.0,   beta=0.60,
                   ma_curta=40.90, ma_longa=39.50, momentum_12m=6.0,  momentum_3m=1.8),
    "VIVT3":  dict(nome="Telefônica Brasil S.A.",   setor="Telecom/Mídia",
                   preco=53.90, dy=5.4,  roe=8.9,  pl=22.0, pvp=1.0,  payout=70,
                   divida_ebitda=1.2,  eps_growth=3.0,   beta=0.55,
                   ma_curta=53.00, ma_longa=52.00, momentum_12m=5.0,  momentum_3m=1.2),
    "CMIG4":  dict(nome="Cemig PN",                 setor="Energia",
                   preco=9.80,  dy=8.9,  roe=14.2, pl=5.2,  pvp=1.3,  payout=58,
                   divida_ebitda=1.8,  eps_growth=-6.0,  beta=1.40,
                   ma_curta=9.60,  ma_longa=9.30,  momentum_12m=4.0,  momentum_3m=1.0),
    "CPLE3":  dict(nome="Companhia Paranaense E.",  setor="Energia",
                   preco=10.25, dy=6.8,  roe=12.3, pl=16.4, pvp=1.5,  payout=48,
                   divida_ebitda=2.9,  eps_growth=-2.0,  beta=0.80,
                   ma_curta=10.30, ma_longa=10.80, momentum_12m=-3.0, momentum_3m=-1.5),
    "ISAE4":  dict(nome="ISA Energia Brasil S.A.",  setor="Energia",
                   preco=22.70, dy=5.9,  roe=12.1, pl=22.6, pvp=1.4,  payout=51,
                   divida_ebitda=3.2,  eps_growth=0.0,   beta=0.60,
                   ma_curta=22.90, ma_longa=23.10, momentum_12m=-2.0, momentum_3m=-0.8),
    "BBDC4":  dict(nome="Banco Bradesco S.A.",      setor="Bancos/Fin.",
                   preco=13.50, dy=4.8,  roe=10.2, pl=9.4,  pvp=0.9,  payout=44,
                   divida_ebitda=None, eps_growth=-12.0, beta=1.15,
                   ma_curta=13.80, ma_longa=14.10, momentum_12m=-6.0, momentum_3m=-2.2),
}

# ─────────────────────────────────────────────────────────────────────────────
#  Backtest demo (valores ilustrativos, exibidos no --demo --backtest)
# ─────────────────────────────────────────────────────────────────────────────

DEMO_BACKTEST = {
    "WEGE3":  {"retorno_pct": +38.4, "capital_final": 13_840.00, "n_trades": 6,  "win_rate_pct": 66.7},
    "PETR4":  {"retorno_pct": +82.3, "capital_final": 18_230.00, "n_trades": 9,  "win_rate_pct": 66.7},
    "ITUB4":  {"retorno_pct": +44.1, "capital_final": 14_410.00, "n_trades": 8,  "win_rate_pct": 62.5},
    "TAEE11": {"retorno_pct": +21.7, "capital_final": 12_170.00, "n_trades": 5,  "win_rate_pct": 60.0},
    "BBAS3":  {"retorno_pct": +36.9, "capital_final": 13_690.00, "n_trades": 7,  "win_rate_pct": 57.1},
    "VALE3":  {"retorno_pct": -8.2,  "capital_final": 9_180.00,  "n_trades": 10, "win_rate_pct": 40.0},
    "EGIE3":  {"retorno_pct": +18.5, "capital_final": 11_850.00, "n_trades": 6,  "win_rate_pct": 50.0},
    "VIVT3":  {"retorno_pct": +12.3, "capital_final": 11_230.00, "n_trades": 4,  "win_rate_pct": 50.0},
    "CMIG4":  {"retorno_pct": +26.8, "capital_final": 12_680.00, "n_trades": 8,  "win_rate_pct": 62.5},
    "CPLE3":  {"retorno_pct": +4.1,  "capital_final": 10_410.00, "n_trades": 5,  "win_rate_pct": 40.0},
    "ISAE4":  {"retorno_pct": +9.6,  "capital_final": 10_960.00, "n_trades": 4,  "win_rate_pct": 50.0},
    "BBDC4":  {"retorno_pct": -12.4, "capital_final": 8_760.00,  "n_trades": 9,  "win_rate_pct": 33.3},
}


def _limpar(ticker: str) -> str:
    return (ticker or "").upper().replace(".SA", "")


def get_demo_fundamentos(ticker: str) -> dict:
    """Fundamentos simulados. Contrato idêntico ao data.fundamentals.get_fundamentos()."""
    t = _limpar(ticker)
    d = DEMO_ACOES.get(t)
    if d is None:
        return {"ticker": t, "delisted": True}
    return {
        "ticker":        t,
        "nome":          d["nome"],
        "setor":         d["setor"],
        "preco":         d["preco"],
        "dy":            d["dy"],
        "roe":           d["roe"],
        "pl":            d["pl"],
        "lpa":           round(d["preco"] / d["pl"], 2) if d["pl"] else None,
        "pvp":           d["pvp"],
        "payout":        d["payout"],
        "divida_ebitda": d["divida_ebitda"],
        "eps_growth":    d["eps_growth"],
        "beta":          d["beta"],
        "delisted":      False,
    }


def get_demo_tecnico(ticker: str) -> dict:
    """Dados técnicos simulados. Contrato idêntico ao data.market_data.get_dados_tecnicos_completos()."""
    t = _limpar(ticker)
    d = DEMO_ACOES.get(t)
    if d is None:
        return {}
    return {
        "preco":          d["preco"],
        "ma_curta":       d["ma_curta"],
        "ma_longa":       d["ma_longa"],
        "tendencia_alta": d["ma_curta"] > d["ma_longa"],
        "momentum_12m":   d["momentum_12m"],
        "momentum_3m":    d["momentum_3m"],
        "beta":           d["beta"],
        "eps_growth":     d["eps_growth"],
        "suporte":        round(d["preco"] * 0.90, 2),
        "resistencia":    round(d["preco"] * 1.08, 2),
    }
