"""
analysis/valuation.py — Preço justo por 3 métodos + média ponderada.

Métodos e regras de exclusão (README + regras recuperadas do gabarito 10/03/2026):
  1. Graham   √(22.5 × LPA × VPA)   — off p/ bancos/FIIs, LPA ≤ 0 ou PVP > 5
  2. DDM      DPS / DY_alvo_setor   — off se DY < 3% (growth) ou DY > cap (yield trap)
  3. P/L justo LPA × P/L_mediano    — off se LPA ≤ 0

Sanity: método descartado se resultado < 30% ou > 250% do preço atual.

Contrato do dict retornado:
  preco_justo, upside, upside_suficiente, div_estimado, div_mensal,
  metodos, qualidade
"""

from math import sqrt

from config.settings import (
    DDM_DY_MIN, GRAHAM_PVP_MAX, UPSIDE_MIN_BUY,
    VALUATION_MIN_RATIO, VALUATION_MAX_RATIO,
)

# Peso de cada método na média (renormalizado entre os que sobrevivem)
_PESOS_METODOS = {"graham": 0.30, "ddm": 0.35, "pl_justo": 0.35}

_QUALIDADE = {3: "alta", 2: "média", 1: "baixa", 0: "indisponível"}


def calcular_valuation(fund: dict, perfil: dict) -> dict:
    preco = fund.get("preco")
    lpa   = fund.get("lpa")
    pvp   = fund.get("pvp")
    dy    = fund.get("dy")                      # pontos percentuais
    dy_frac = (dy / 100) if dy is not None else None

    vazio = {"preco_justo": None, "upside": None, "upside_suficiente": False,
             "div_estimado": None, "div_mensal": None, "metodos": {},
             "qualidade": _QUALIDADE[0]}
    if not preco or preco <= 0:
        return vazio

    metodos = {}

    # ── 1. Graham ─────────────────────────────────────────────────────────────
    if (perfil.get("graham", True) and lpa is not None and lpa > 0
            and pvp is not None and 0 < pvp <= GRAHAM_PVP_MAX):
        vpa = preco / pvp
        metodos["graham"] = round(sqrt(22.5 * lpa * vpa), 2)

    # ── 2. DDM ────────────────────────────────────────────────────────────────
    if (dy_frac is not None and DDM_DY_MIN <= dy_frac <= perfil["dy_cap"]):
        dps = preco * dy_frac
        metodos["ddm"] = round(dps / perfil["dy_alvo"], 2)

    # ── 3. P/L justo ──────────────────────────────────────────────────────────
    if lpa is not None and lpa > 0:
        metodos["pl_justo"] = round(lpa * perfil["pl_mediano"], 2)

    # ── Sanity: descarta métodos fora de 30%–250% do preço atual ─────────────
    metodos = {m: v for m, v in metodos.items()
               if VALUATION_MIN_RATIO * preco <= v <= VALUATION_MAX_RATIO * preco}

    # ── Média ponderada dos sobreviventes ────────────────────────────────────
    if metodos:
        soma_pesos  = sum(_PESOS_METODOS[m] for m in metodos)
        preco_justo = round(sum(v * _PESOS_METODOS[m] for m, v in metodos.items()) / soma_pesos, 2)
        upside      = round((preco_justo / preco - 1) * 100, 1)
    else:
        preco_justo = upside = None

    div_estimado = round(preco * dy_frac, 2) if dy_frac else None

    return {
        "preco_justo":       preco_justo,
        "upside":            upside,
        "upside_suficiente": (upside is not None and upside >= UPSIDE_MIN_BUY),
        "div_estimado":      div_estimado,
        "div_mensal":        round(div_estimado / 12, 2) if div_estimado else None,
        "metodos":           metodos,
        "qualidade":         _QUALIDADE[len(metodos)],
    }
