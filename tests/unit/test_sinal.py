from analysis.dividend_analysis import analisar_ativo, sinal_fundamentalista
from config.settings import PERFIS_SETOR


# Fund aprovado (petroleo) com valuation folgado -> upside alto e robusto.
def _fund_petr4():
    return {"ticker": "PETR4", "setor": None, "preco": 10, "lpa": 3, "pvp": 1.5,
            "dy": 11, "roe": 20, "pl": 5, "divida_ebitda": 1.0, "payout": 40,
            "eps_growth": None, "beta": None}


def test_buy_exige_upside_e_tendencia():
    r = analisar_ativo(_fund_petr4(), {"tendencia_alta": True, "ma_longa": 9})
    assert r["valuation"]["upside_suficiente"] is True
    assert r["sinal"] == "BUY"


def test_tendencia_baixa_vira_hold():
    r = analisar_ativo(_fund_petr4(), {"tendencia_alta": False, "ma_longa": 9})
    assert r["sinal"] == "HOLD"


def test_upside_insuficiente_vira_hold():
    # WEGE3-like (industrial/GROWTH): aprovado mas preco justo ~= preco -> HOLD
    fund = {"ticker": "WEGE3", "setor": None, "preco": 100, "lpa": 3.8, "pvp": 10,
            "dy": 2.5, "roe": 32, "pl": 26, "divida_ebitda": 0.5, "payout": 20,
            "eps_growth": None, "beta": None}
    r = analisar_ativo(fund, {"tendencia_alta": True, "ma_longa": 90})
    assert r["sinal"] == "HOLD"


def test_divida_estrutural_nao_gera_sell_sozinha():
    # energia: divida 4.0 > teto 3.5, mas lucro NAO caiu -> nao e SELL
    perfil = PERFIS_SETOR["energia"]
    fund = {"dy": 7, "roe": 18, "pl": 14, "divida_ebitda": 4.0,
            "payout": 50, "eps_growth": None, "lpa": 2}
    assert sinal_fundamentalista(fund, perfil) != "SELL"
