from analysis.valuation import calcular_valuation
from config.settings import PERFIS_SETOR, resolver_perfil


def _perfil(nome="default"):
    return PERFIS_SETOR[nome]


def test_graham_valor():
    # lpa=5, vpa=20 (preco=100, pvp=5) -> sqrt(22.5*5*20) = 47.43
    fund = {"preco": 100, "lpa": 5, "pvp": 5, "dy": None}
    v = calcular_valuation(fund, _perfil("default"))
    assert v["metodos"]["graham"] == 47.43


def test_graham_lpa_negativo_none():
    fund = {"preco": 100, "lpa": -5, "pvp": 2, "dy": None}
    v = calcular_valuation(fund, _perfil("default"))
    assert "graham" not in v["metodos"]


def test_ddm_acima_do_cap_descartado():
    # dy 15% > dy_cap default (0.13) -> DDM nao participa
    fund = {"preco": 100, "lpa": None, "pvp": None, "dy": 15}
    v = calcular_valuation(fund, _perfil("default"))
    assert "ddm" not in v["metodos"]


def test_ddm_valor_razoavel():
    # dy 8%, dy_alvo 0.075 (energia) -> ddm = 8/0.075 ~ 106.67
    fund = {"preco": 100, "lpa": None, "pvp": None, "dy": 8}
    v = calcular_valuation(fund, _perfil("energia"))
    assert 100 <= v["metodos"]["ddm"] <= 115


def test_sanity_preco_justo_absurdo_none():
    # unico metodo (pl_justo=1200) >> 250% de 10 -> descartado -> preco_justo None
    fund = {"preco": 10, "lpa": 100, "pvp": None, "dy": None}
    v = calcular_valuation(fund, _perfil("default"))
    assert v["preco_justo"] is None


def test_graham_desativado_para_banco():
    _, perfil = resolver_perfil("ITUB4")  # bancos -> graham=False
    fund = {"preco": 50, "lpa": 5, "pvp": 1, "dy": None}
    v = calcular_valuation(fund, perfil)
    assert "graham" not in v["metodos"]
