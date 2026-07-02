"""
analysis/dividend_analysis.py — O cérebro: score multi-fator + sinal BUY/SELL/HOLD.

Três responsabilidades (construídas e testadas separadamente):
  1. calcular_score(fund, perfil)        → float 0–10
  2. sinal_fundamentalista(fund, perfil) → "BUY" | "SELL" | "HOLD"
  3. analisar_ativo(fund, tec, ...)      → dict completo p/ tabela, HTML e alertas

Unidades: dy/roe/payout/eps_growth em pontos percentuais (ver data/fundamentals.py).
Fatores com dado ausente (eps_growth, beta) são ignorados e os pesos
renormalizados — ausência não penaliza (README).
"""

from config.settings import (
    FILTRO_DIVIDA_MAX, FILTRO_DY_MIN, FILTRO_ROE_MIN, PESOS_SCORE,
    STOP_LOSS_PCT, TAKE_PROFIT_PCT, resolver_perfil,
)
from analysis.valuation import calcular_valuation


# ─────────────────────────────────────────────────────────────────────────────
#  1. Score multi-fator (0–10)
# ─────────────────────────────────────────────────────────────────────────────

def _nota_dy(dy, perfil):
    if dy is None:
        return 1.0                                # não paga dividendo
    if dy > perfil["dy_cap"] * 100:
        return 3.0                                # yield trap: alto demais suspeita
    ratio = dy / (perfil["dy_alvo"] * 100)
    if ratio >= 1.20: return 10.0
    if ratio >= 1.00: return 9.0
    if ratio >= 0.85: return 7.0
    if ratio >= 0.70: return 5.0
    if ratio >= 0.50: return 3.0
    return 1.0


def _nota_roe(roe):
    if roe is None:
        return 3.0
    return max(0.0, min(10.0, roe / 3.0))         # 30% de ROE = nota 10


def _nota_pl(pl, perfil):
    if pl is None or pl <= 0:
        return 2.0                                # prejuízo ou indisponível
    if perfil["pl_min"] <= pl <= perfil["pl_max"]:
        return 9.0
    if pl < perfil["pl_min"]:
        return 7.0                                # barato — pode ser value trap
    excesso = (pl - perfil["pl_max"]) / perfil["pl_max"]
    return max(2.0, 9.0 - excesso * 12.0)         # caro: decai com o excesso


def _nota_divida(divida):
    if divida is None:
        return 6.0                                # bancos etc. — neutro, não penaliza
    if divida <= 1.0: return 9.0
    if divida <= 2.0: return 7.0
    if divida <= 3.0: return 4.0
    return 2.0


def _nota_payout(payout):
    if payout is None:
        return 5.0
    if 30 <= payout <= 70: return 9.0             # zona saudável
    if 70 < payout <= 90:  return 6.0
    if 10 <= payout < 30:  return 7.0             # retém muito, mas sustentável
    if payout > 90:        return 2.0             # insustentável
    return 4.0                                    # < 10%


def _nota_eps_growth(eps):
    if eps >= 15:  return 10.0
    if eps >= 8:   return 8.0
    if eps >= 3:   return 6.0
    if eps >= 0:   return 5.0
    if eps >= -10: return 3.0
    return 1.0


def _nota_beta(beta):
    if beta <= 0.80: return 9.0
    if beta <= 1.05: return 7.0
    if beta <= 1.35: return 5.0
    if beta <= 1.70: return 3.0
    return 2.0


def calcular_score(fund: dict, perfil: dict) -> float:
    """
    Score 0–10 ponderado pela estratégia do perfil (DIVIDENDO ou GROWTH).
    eps_growth e beta ausentes são excluídos com renormalização dos pesos.
    """
    pesos = PESOS_SCORE[perfil["estrategia"]]

    notas = {
        "dy":     _nota_dy(fund.get("dy"), perfil),
        "roe":    _nota_roe(fund.get("roe")),
        "pl":     _nota_pl(fund.get("pl"), perfil),
        "divida": _nota_divida(fund.get("divida_ebitda")),
        "payout": _nota_payout(fund.get("payout")),
    }
    # Fatores opcionais: só entram se o dado existir
    if fund.get("eps_growth") is not None:
        notas["eps_growth"] = _nota_eps_growth(fund["eps_growth"])
    if fund.get("beta") is not None:
        notas["beta"] = _nota_beta(fund["beta"])

    soma_pesos = sum(pesos[f] for f in notas)
    score = sum(notas[f] * pesos[f] for f in notas) / soma_pesos
    return round(score, 2)


# ─────────────────────────────────────────────────────────────────────────────
#  2. Sinal fundamentalista
# ─────────────────────────────────────────────────────────────────────────────

def _avaliar_fundamentos(fund: dict, perfil: dict):
    """
    Retorna (sinal, motivos).
      SELL — fundamentos deteriorados (qualquer gatilho abaixo)
      BUY  — fundamentos aprovados pelos filtros da estratégia
      HOLD — nem deteriorado, nem aprovado
    O sinal BUY aqui é "elegível": o analisar_ativo ainda exige
    upside suficiente + tendência de alta para confirmar.
    """
    dy     = fund.get("dy")
    roe    = fund.get("roe")
    lpa    = fund.get("lpa")
    payout = fund.get("payout")
    divida = fund.get("divida_ebitda")
    eps    = fund.get("eps_growth")

    # ── Gatilhos de deterioração → SELL ──────────────────────────────────────
    motivos = []
    if lpa is not None and lpa < 0:
        motivos.append("prejuízo (LPA negativo)")
    if payout is not None and payout > 110:
        motivos.append(f"payout insustentável ({payout:.0f}%)")
    if dy is not None and dy > perfil["dy_cap"] * 100:
        motivos.append(f"possível yield trap (DY {dy:.1f}%)")
    if roe is not None and roe < 5:
        motivos.append(f"ROE muito baixo ({roe:.1f}%)")
    if divida is not None and divida > 4:
        motivos.append(f"dívida excessiva ({divida:.1f}x EBITDA)")
    if motivos:
        return "SELL", motivos

    # ── Filtros de aprovação por estratégia ──────────────────────────────────
    divida_ok = divida is None or divida <= FILTRO_DIVIDA_MAX
    roe_ok    = roe is not None and roe >= FILTRO_ROE_MIN * 100

    if perfil["estrategia"] == "GROWTH":
        eps_ok = eps is None or eps >= 8          # ausente não reprova (README)
        aprovado = roe_ok and eps_ok and divida_ok
    else:  # DIVIDENDO
        dy_ok    = dy is not None and dy >= FILTRO_DY_MIN * 100
        aprovado = dy_ok and roe_ok and divida_ok

    return ("BUY", []) if aprovado else ("HOLD", [])


def sinal_fundamentalista(fund: dict, perfil: dict) -> str:
    """Apenas o sinal, sem os motivos (contrato simples p/ testes e reuso)."""
    return _avaliar_fundamentos(fund, perfil)[0]


# ─────────────────────────────────────────────────────────────────────────────
#  3. Análise completa de um ativo
# ─────────────────────────────────────────────────────────────────────────────

def analisar_ativo(fund: dict, tec: dict, preco_compra: float = 0) -> dict:
    """
    Junta score + sinal + valuation + níveis técnicos num dict único,
    no formato consumido pelo main.py, console_alert e html_report.

    Sinal BUY final exige as 3 condições (README):
      fundamentos aprovados + upside >= 10% + tendência de alta (MA50 > MA200).
    """
    tec = tec or {}
    ticker = fund.get("ticker", "")
    nome_perfil, perfil = resolver_perfil(ticker, fund.get("setor"))

    score          = calcular_score(fund, perfil)
    sinal, motivos = _avaliar_fundamentos(fund, perfil)
    valuation      = calcular_valuation(fund, perfil)
    alertas        = list(motivos)

    # ── Confirmação do BUY: upside + tendência ────────────────────────────────
    tendencia_alta = tec.get("tendencia_alta")
    if sinal == "BUY":
        if not valuation["upside_suficiente"]:
            sinal = "HOLD"
            if valuation["upside"] is not None:
                alertas.append(f"upside insuficiente ({valuation['upside']:+.0f}%)")
            else:
                alertas.append("valuation indisponível")
        elif tendencia_alta is False:
            sinal = "HOLD"
            alertas.append("tendência de baixa (MA50 < MA200)")

    # ── Alertas informativos ──────────────────────────────────────────────────
    preco = fund.get("preco")
    ma_l  = tec.get("ma_longa")
    if preco is not None and ma_l is not None and preco < ma_l:
        alertas.append("preço abaixo da MA200")
    payout = fund.get("payout")
    if payout is not None and 90 < payout <= 110:
        alertas.append(f"payout alto ({payout:.0f}%)")

    # ── Níveis técnicos e posição (se informado preço de compra) ─────────────
    niveis = {
        "suporte":       tec.get("suporte"),
        "resistencia":   tec.get("resistencia"),
        "stop_sugerido": round(preco * (1 + STOP_LOSS_PCT), 2) if preco else None,
        "alvo_sugerido": round(preco * (1 + TAKE_PROFIT_PCT), 2) if preco else None,
    }

    posicao = None
    if preco_compra and preco:
        var = (preco / preco_compra - 1)
        posicao = {"preco_compra": preco_compra, "variacao_pct": round(var * 100, 1)}
        if var <= STOP_LOSS_PCT:
            alertas.append(f"STOP LOSS atingido ({var * 100:+.1f}%)")
        elif var >= TAKE_PROFIT_PCT:
            alertas.append(f"TAKE PROFIT atingido ({var * 100:+.1f}%)")

    return {
        "ticker":          ticker,
        "setor_perfil":    perfil["label"],
        "estrategia":      perfil["estrategia"],
        "score":           score,
        "sinal":           sinal,
        "alertas":         alertas,
        "fundamentos":     fund,
        "tecnico":         tec,
        "valuation":       valuation,
        "niveis_tecnicos": niveis,
        "posicao":         posicao,
    }
