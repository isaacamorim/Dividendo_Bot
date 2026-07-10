from analysis.dividend_analysis import calcular_score, _nota_payout_fii
from config.settings import PERFIS_SETOR, resolver_perfil


def _perfil(nome="default"):
    return PERFIS_SETOR[nome]


def test_score_dict_completo_entre_0_e_10():
    fund = {"dy": 7.0, "roe": 18, "pl": 9, "divida_ebitda": 1.5,
            "payout": 45, "eps_growth": 5, "beta": 0.9}
    s = calcular_score(fund, _perfil("bancos"))
    assert 0 <= s <= 10


def test_score_tudo_none_nao_estoura():
    fund = {"dy": None, "roe": None, "pl": None, "divida_ebitda": None,
            "payout": None, "eps_growth": None, "beta": None}
    s = calcular_score(fund, _perfil("default"))
    assert 0 <= s <= 10


def test_score_petr4_mock_alto():
    _, perfil = resolver_perfil("PETR4")  # petroleo
    fund = {"dy": 10, "roe": 25, "pl": 5, "divida_ebitda": 1.4,
            "payout": 38, "eps_growth": -8, "beta": 1.3}
    s = calcular_score(fund, perfil)
    assert 7 <= s <= 10


def test_score_empresa_ruim_baixo():
    fund = {"dy": 0, "roe": 2, "pl": 50, "divida_ebitda": None,
            "payout": None, "eps_growth": None, "beta": None}
    s = calcular_score(fund, _perfil("default"))
    assert s < 4


def test_score_fii_dy_alto_acima_de_5():
    # FII com DY >= 8% deve pontuar >= 5 (aceite Frente 4c). ROE/PL/dívida
    # não entram; score vem de DY, payout e P/VP.
    _, perfil = resolver_perfil("HGLG11")           # perfil "fii" (estrategia FII)
    assert perfil["estrategia"] == "FII"
    fund = {"dy": 8.9, "payout": 83.5, "pvp": 0.94, "roe": None,
            "pl": None, "divida_ebitda": None, "eps_growth": None, "beta": None}
    s = calcular_score(fund, perfil)
    assert s >= 5


def test_score_fii_sem_pvp_nao_estoura():
    # FII de papel não reporta P/VP — score deve renormalizar sem quebrar.
    _, perfil = resolver_perfil("KNIP11")
    fund = {"dy": 10.8, "payout": 99.1, "pvp": None, "roe": None,
            "pl": None, "divida_ebitda": None, "eps_growth": None, "beta": None}
    s = calcular_score(fund, perfil)
    assert 0 <= s <= 10


def test_nota_payout_fii():
    # FII: payout alto (90-100%) é obrigatório por lei = saúde, não penaliza.
    assert _nota_payout_fii(95) == 1.0
    assert _nota_payout_fii(60) == 0.4
    assert _nota_payout_fii(None) is None


def test_score_fii_payout_furado_ignorado():
    # yfinance às vezes dá payout absurdo p/ FII (ex.: 3%). Deve ser dropado
    # (dado furado), não penalizar como empresa ruim.
    _, perfil = resolver_perfil("HGLG11")
    base = {"dy": 9.8, "pvp": 0.9, "roe": None, "pl": None,
            "divida_ebitda": None, "eps_growth": None, "beta": None}
    furado = calcular_score({**base, "payout": 3}, perfil)      # < 30 → dropa o fator
    sem = calcular_score({**base, "payout": None}, perfil)      # sem payout
    saudavel = calcular_score({**base, "payout": 95}, perfil)   # distribui quase tudo
    assert furado == sem                                        # furado == ausente (dropado)
    assert saudavel > furado                                    # payout saudável pontua mais


def test_resolver_perfil_respeita_label_da_watchlist():
    # HSML11 (FII de shopping) não está no TICKER_PERFIL e o yfinance reporta
    # sector "Financial Services" — sem a watchlist cairia em bancos.
    nome_sem, _ = resolver_perfil("HSML11", "Financial Services")
    assert nome_sem == "bancos"
    # Com o label "FII" escolhido na UI, resolve como FII.
    nome_com, perfil = resolver_perfil("HSML11", "Financial Services", "FII")
    assert nome_com == "fii"
    assert perfil["label"] == "FII"
    # Transmissoras NÃO são sobrescritas pelo label genérico "Energia".
    nome_tx, _ = resolver_perfil("TAEE11", None, "Energia")
    assert nome_tx == "transmissao"
