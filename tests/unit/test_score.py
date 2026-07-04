from analysis.dividend_analysis import calcular_score
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
