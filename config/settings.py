"""
config/settings.py — Watchlist, filtros, perfis por setor e parâmetros de risco.

Reconstruído em jul/2026 a partir do README + gabarito de 10/03/2026
(reports/relatorio_20260310_1724.html).
"""

# ─────────────────────────────────────────────────────────────────────────────
#  Watchlist (12 tickers do gabarito de março/2026)
# ─────────────────────────────────────────────────────────────────────────────

WATCHLIST_ACOES = [
    # Bancos
    "BBAS3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    # Energia
    "TAEE11.SA",
    "ISAE4.SA",
    "CMIG4.SA",
    "CPLE3.SA",
    "EGIE3.SA",
    # Commodities
    "PETR4.SA",
    "VALE3.SA",
    # Telecom
    "VIVT3.SA",
    # Industrial
    "WEGE3.SA",
    # Tecnologia
    "TOTS3.SA",
    # Saúde
    "RADL3.SA",
    "RDOR3.SA",
    # Consumo
    "ABEV3.SA",
    "LREN3.SA",
    # Seguros
    "CXSE3.SA",
    # Papel e Celulose
    "SUZB3.SA",
    # Shopping
    "MULT3.SA",
]

# ─────────────────────────────────────────────────────────────────────────────
#  Watchlist de FIIs (Fundos Imobiliários — distribuem proventos mensais)
#  Todos validados no yfinance (preço + histórico + proventos ao vivo).
# ─────────────────────────────────────────────────────────────────────────────

WATCHLIST_FIIS = [
    "HGLG11.SA",   # logística
    "XPML11.SA",   # shoppings
    "MXRF11.SA",   # papel / híbrido
    "KNRI11.SA",   # lajes + logística
    "VISC11.SA",   # shoppings
    "KNIP11.SA",   # papel (CRI indexado ao IPCA)
    "BRCO11.SA",   # logística
    "RBRF11.SA",   # fundo de fundos
]

# Universo completo do scan (ações + FIIs)
WATCHLIST_COMPLETA = WATCHLIST_ACOES + WATCHLIST_FIIS

# ─────────────────────────────────────────────────────────────────────────────
#  Filtros de compra (fundamentos mínimos — frações, ex.: 0.06 = 6%)
# ─────────────────────────────────────────────────────────────────────────────

FILTRO_DY_MIN     = 0.06   # DY mínimo p/ estratégia DIVIDENDO
FILTRO_ROE_MIN    = 0.15   # ROE mínimo
FILTRO_DIVIDA_MAX = 2.0    # Dívida/EBITDA máxima (não se aplica a bancos)

# ─────────────────────────────────────────────────────────────────────────────
#  Gestão de risco (backtest e alertas de posição)
# ─────────────────────────────────────────────────────────────────────────────

STOP_LOSS_PCT   = -0.08    # -8%
TAKE_PROFIT_PCT = +0.20    # +20%
MA_CURTA        = 50
MA_LONGA        = 200

# ─────────────────────────────────────────────────────────────────────────────
#  Alertas / sinal
# ─────────────────────────────────────────────────────────────────────────────

SCORE_MIN_ALERTA = 6.0     # score mínimo p/ alerta de compra
UPSIDE_MIN_BUY   = 10.0    # upside mínimo (%) p/ sinal BUY

# ─────────────────────────────────────────────────────────────────────────────
#  Valuation — sanity check
#  Preço justo descartado se < 30% ou > 250% do preço atual.
#  DDM exige DY >= DDM_DY_MIN (evita preço justo sem sentido p/ growth).
# ─────────────────────────────────────────────────────────────────────────────

VALUATION_MIN_RATIO = 0.30
VALUATION_MAX_RATIO = 2.50
DDM_DY_MIN          = 0.03   # DDM só participa se DY atual >= 3%
GRAHAM_PVP_MAX      = 5.0    # Graham desativado se PVP > 5

# ─────────────────────────────────────────────────────────────────────────────
#  Transmissoras — P/L estrutural alto, detectadas por ticker
# ─────────────────────────────────────────────────────────────────────────────

TRANSMISSORAS = {"TAEE11", "ISAE4", "TRPL4", "ENGI11"}

# ─────────────────────────────────────────────────────────────────────────────
#  Perfis por setor
#    pl_min/pl_max : faixa saudável de P/L
#    pl_mediano    : usado no método "P/L justo"
#    dy_alvo       : DY usado no DDM (fração)
#    dy_cap        : acima disso = suspeita de yield trap (fração)
#    estrategia    : define os pesos do score
#    graham        : False = método Graham desativado p/ o setor
# ─────────────────────────────────────────────────────────────────────────────

#    divida_max    : Dívida/EBITDA tolerada como ESTRUTURAL do setor (não é risco).
#                    Concessões reguladas (transmissão/energia) operam alavancadas
#                    de propósito — 3–5x EBITDA é normal, não deterioração.
#                    None = métrica não se aplica (bancos não têm EBITDA).

PERFIS_SETOR = {
    "bancos":      {"label": "Bancos/Fin.",       "pl_min": 7,  "pl_max": 13, "pl_mediano": 9,
                    "dy_alvo": 0.065, "dy_cap": 0.13, "divida_max": None, "estrategia": "DIVIDENDO", "graham": False},
    "energia":     {"label": "Energia",           "pl_min": 12, "pl_max": 16, "pl_mediano": 14,
                    "dy_alvo": 0.075, "dy_cap": 0.15, "divida_max": 3.5,  "estrategia": "DIVIDENDO", "graham": True},
    "transmissao": {"label": "Energia",           "pl_min": 28, "pl_max": 38, "pl_mediano": 32,
                    "dy_alvo": 0.070, "dy_cap": 0.14, "divida_max": 5.5,  "estrategia": "DIVIDENDO", "graham": True},
    "petroleo":    {"label": "Petróleo/Gás",      "pl_min": 4,  "pl_max": 8,  "pl_mediano": 6,
                    "dy_alvo": 0.085, "dy_cap": 0.18, "divida_max": 2.5,  "estrategia": "DIVIDENDO", "graham": True},
    "commodities": {"label": "Commodities",       "pl_min": 5,  "pl_max": 10, "pl_mediano": 7,
                    "dy_alvo": 0.055, "dy_cap": 0.14, "divida_max": 2.5,  "estrategia": "DIVIDENDO", "graham": True},
    "telecom":     {"label": "Telecom/Mídia",     "pl_min": 12, "pl_max": 20, "pl_mediano": 15,
                    "dy_alvo": 0.055, "dy_cap": 0.12, "divida_max": 3.0,  "estrategia": "DIVIDENDO", "graham": True},
    "industrial":  {"label": "Industrial/Growth", "pl_min": 20, "pl_max": 35, "pl_mediano": 27,
                    "dy_alvo": 0.025, "dy_cap": 0.06, "divida_max": 2.5,  "estrategia": "GROWTH",    "graham": True},
    "tecnologia":  {"label": "Tecnologia",        "pl_min": 20, "pl_max": 40, "pl_mediano": 28,
                    "dy_alvo": 0.020, "dy_cap": 0.06, "divida_max": 2.5,  "estrategia": "GROWTH",    "graham": True},
    "saude":       {"label": "Saúde",             "pl_min": 14, "pl_max": 30, "pl_mediano": 20,
                    "dy_alvo": 0.020, "dy_cap": 0.07, "divida_max": 3.0,  "estrategia": "GROWTH",    "graham": True},
    "consumo":     {"label": "Consumo",           "pl_min": 12, "pl_max": 25, "pl_mediano": 18,
                    "dy_alvo": 0.040, "dy_cap": 0.10, "divida_max": 2.5,  "estrategia": "DIVIDENDO", "graham": True},
    "seguros":     {"label": "Seguros",           "pl_min": 8,  "pl_max": 16, "pl_mediano": 11,
                    "dy_alvo": 0.060, "dy_cap": 0.13, "divida_max": None, "estrategia": "DIVIDENDO", "graham": False},
    "papel":       {"label": "Papel/Celulose",    "pl_min": 5,  "pl_max": 12, "pl_mediano": 8,
                    "dy_alvo": 0.050, "dy_cap": 0.14, "divida_max": 3.5,  "estrategia": "DIVIDENDO", "graham": True},
    "shopping":    {"label": "Shopping",          "pl_min": 10, "pl_max": 18, "pl_mediano": 14,
                    "dy_alvo": 0.050, "dy_cap": 0.12, "divida_max": 3.5,  "estrategia": "DIVIDENDO", "graham": True},
    "infraestrutura": {"label": "Infraestrutura", "pl_min": 12, "pl_max": 20, "pl_mediano": 16,
                    "dy_alvo": 0.040, "dy_cap": 0.11, "divida_max": 4.0,  "estrategia": "DIVIDENDO", "graham": True},
    "fii":         {"label": "FII",               "pl_min": 10, "pl_max": 18, "pl_mediano": 12,
                    "dy_alvo": 0.090, "dy_cap": 0.18, "divida_max": None, "estrategia": "FII",
                    "graham": False, "paga_mensal": True, "pvp_ideal": 1.05},
    "default":     {"label": "Geral",             "pl_min": 8,  "pl_max": 18, "pl_mediano": 12,
                    "dy_alvo": 0.060, "dy_cap": 0.13, "divida_max": 3.0,  "estrategia": "DIVIDENDO", "graham": True},
}

# Perfil fixo por ticker (mais confiável que o setor do Yahoo p/ a watchlist)
TICKER_PERFIL = {
    # Bancos
    "BBAS3": "bancos",
    "ITUB4": "bancos",
    "BBDC4": "bancos",
    "SANB11": "bancos",
    # Seguros
    "CXSE3": "seguros",
    "PSSA3": "seguros",
    # Transmissão
    "TAEE11": "transmissao",
    "ISAE4": "transmissao",
    "TRPL4": "transmissao",
    # Energia
    "CMIG4": "energia",
    "CPLE3": "energia",
    "CPLE6": "energia",
    "EGIE3": "energia",
    # Petróleo
    "PETR3": "petroleo",
    "PETR4": "petroleo",
    "PRIO3": "petroleo",
    # Commodities / Mineração / Siderurgia
    "VALE3": "commodities",
    "CSNA3": "commodities",
    "GGBR4": "commodities",
    # Papel e Celulose
    "SUZB3": "papel",
    "KLBN11": "papel",
    # Telecom
    "VIVT3": "telecom",
    "TIMS3": "telecom",
    # Tecnologia
    "TOTS3": "tecnologia",
    # Industrial
    "WEGE3": "industrial",
    # Saúde
    "RADL3": "saude",
    "RDOR3": "saude",
    # Consumo
    "ABEV3": "consumo",
    "LREN3": "consumo",
    # Infraestrutura / Concessões
    "CCRO3": "infraestrutura",
    # Shopping Centers
    "MULT3": "shopping",
    # FIIs (Fundos Imobiliários)
    "HGLG11": "fii",
    "XPML11": "fii",
    "MXRF11": "fii",
    "KNRI11": "fii",
    "VISC11": "fii",
    "KNIP11": "fii",
    "BRCO11": "fii",
    "RBRF11": "fii",
}

# Fallback: setor do Yahoo Finance → perfil (p/ tickers fora do TICKER_PERFIL)
SETOR_MAP = {
    "Financial Services": "bancos",
    "Utilities": "energia",
    "Energy": "petroleo",
    "Basic Materials": "commodities",
    "Communication Services": "telecom",
    "Technology": "tecnologia",
    "Healthcare": "saude",
    "Consumer Defensive": "consumo",
    "Consumer Cyclical": "consumo",
    "Industrials": "industrial",
    "Real Estate": "fii",
}


def perfil_por_label(label: str):
    """(nome, perfil) do primeiro perfil cujo label bate. None se não achar.
    Labels não são únicos (ex.: 'Energia' = energia e transmissao) — a 1ª
    ocorrência (a genérica) ganha; casos especiais vêm de TRANSMISSORAS/TICKER_PERFIL."""
    if not label:
        return None
    for nome, p in PERFIS_SETOR.items():
        if nome != "default" and p["label"] == label:
            return nome, p
    return None


def resolver_perfil(ticker: str, setor_yf: str = None, label_watchlist: str = None):
    """
    Resolve o perfil setorial de um ativo.
    Prioridade: transmissoras > TICKER_PERFIL > label da watchlist > SETOR_MAP > default.
    O label da watchlist (escolha manual do usuário na UI) vale mais que o setor do
    Yahoo, mas menos que os mapas fixos (transmissoras não viram 'energia' à toa).
    Retorna (nome_perfil, dict_perfil).
    """
    t = (ticker or "").upper().replace(".SA", "")
    if t in TRANSMISSORAS:
        return "transmissao", PERFIS_SETOR["transmissao"]
    if t in TICKER_PERFIL:
        nome = TICKER_PERFIL[t]
    else:
        por_label = perfil_por_label(label_watchlist)
        if por_label is not None:
            nome = por_label[0]
        elif setor_yf and setor_yf in SETOR_MAP:
            nome = SETOR_MAP[setor_yf]
        else:
            nome = "default"
    # À prova de futuro: setor mapeado sem perfil cai no default em vez de estourar.
    if nome not in PERFIS_SETOR:
        nome = "default"
    return nome, PERFIS_SETOR[nome]


# ─────────────────────────────────────────────────────────────────────────────
#  Pesos do score por estratégia (soma = 1.0)
#  Fatores com dado ausente (eps_growth, beta) são ignorados e os pesos
#  restantes renormalizados — não penaliza (ver README).
# ─────────────────────────────────────────────────────────────────────────────

PESOS_SCORE = {
    "DIVIDENDO": {"dy": 0.30, "roe": 0.20, "pl": 0.15, "divida": 0.15,
                  "payout": 0.10, "eps_growth": 0.05, "beta": 0.05},
    "GROWTH":    {"eps_growth": 0.25, "roe": 0.25, "pl": 0.15, "divida": 0.15,
                  "beta": 0.10, "payout": 0.05, "dy": 0.05},
    # FIIs: sem ROE/P-L/EBITDA relevantes — valor vem de DY, payout e P/VP.
    "FII":       {"dy": 0.40, "payout": 0.20, "pvp": 0.20,
                  "beta": 0.10, "momentum": 0.10},
}
