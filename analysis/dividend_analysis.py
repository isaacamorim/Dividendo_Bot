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
    FILTRO_DY_MIN, FILTRO_ROE_MIN, PESOS_SCORE,
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


def _norm_pvp_fii(pvp):
    """Normaliza o P/VP de um FII em [0,1] (1 = barato sobre o valor patrimonial)."""
    if pvp is None: return None
    if pvp <= 0.95: return 1.0
    if pvp <= 1.05: return 0.8
    if pvp <= 1.15: return 0.5
    if pvp <= 1.30: return 0.2
    return 0.0


def _nota_payout_fii(payout):
    """Payout de FII em [0,1]. Distribuir 90–100% é obrigatório por lei = saúde,
    não risco (ao contrário de empresas). Payout baixo é que preocupa."""
    if payout is None: return None
    if payout >= 85: return 1.0                   # ótimo — cumpre a lei
    if payout >= 70: return 0.7                   # aceitável
    if payout >= 50: return 0.4                   # abaixo do esperado
    return 0.0                                    # problemático


def _nota_momentum(mom):
    """Nota 0–10 pelo momentum de preço (% em 12m, ou 3m como fallback)."""
    if mom >= 15:  return 9.0
    if mom >= 5:   return 7.0
    if mom >= -5:  return 5.0
    if mom >= -15: return 3.0
    return 1.0


def _score_fii(fund: dict, perfil: dict) -> float:
    """
    Score de FII: dominado por DY, payout e P/VP. ROE, P/L e dívida não se
    aplicam (peso 0). beta e momentum entram só se o dado existir (renormaliza).
    """
    pesos = PESOS_SCORE["FII"]
    notas = {"dy": _nota_dy(fund.get("dy"), perfil)}
    payout = fund.get("payout")
    # payout < 30% num FII é quase sempre dado furado do yfinance (FII distribui
    # ~95% por lei) — dropa o fator e renormaliza em vez de penalizar como empresa ruim.
    pay_norm = None if (payout is not None and payout < 30) else _nota_payout_fii(payout)
    if pay_norm is not None:
        notas["payout"] = pay_norm * 10.0     # devolve 0–1; escala p/ 0–10
    pvp_norm = _norm_pvp_fii(fund.get("pvp"))
    if pvp_norm is not None:
        notas["pvp"] = pvp_norm * 10.0        # _norm_pvp_fii devolve 0–1; escala p/ 0–10
    mom = fund.get("momentum_12m")
    if mom is None:
        mom = fund.get("momentum_3m")         # FIIs têm ~250 pregões (<252) → usa o 3m
    if mom is not None:
        notas["momentum"] = _nota_momentum(mom)
    if fund.get("beta") is not None:
        notas["beta"] = _nota_beta(fund["beta"])

    soma_pesos = sum(pesos[f] for f in notas)
    return round(sum(notas[f] * pesos[f] for f in notas) / soma_pesos, 2)


def calcular_score(fund: dict, perfil: dict) -> float:
    """
    Score 0–10 ponderado pela estratégia do perfil (DIVIDENDO, GROWTH ou FII).
    eps_growth e beta ausentes são excluídos com renormalização dos pesos.
    """
    if perfil["estrategia"] == "FII":
        return _score_fii(fund, perfil)

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

def _avaliar_fii(fund: dict, perfil: dict):
    """
    Sinal de FII por DY / P-VP / payout — não usa LPA, ROE nem P/L.
      BUY  — DY >= 8% E P/VP <= 1.10 E payout >= 85% (FII saudável distribui ~95%)
      SELL — DY < 5% OU P/VP > 1.40 (yield fraco ou caro demais sobre o VP)
      HOLD — resto (inclui dados ausentes: conservador)
    """
    dy     = fund.get("dy")
    pvp    = fund.get("pvp")
    payout = fund.get("payout")

    motivos = []
    if dy is not None and dy < 5.0:
        motivos.append(f"DY baixo p/ FII ({dy:.1f}%)")
    if pvp is not None and pvp > 1.40:
        motivos.append(f"P/VP esticado ({pvp:.2f})")
    if motivos:
        return "SELL", motivos

    if (dy is not None and dy >= 8.0 and pvp is not None and pvp <= 1.10
            and payout is not None and payout >= 85):
        return "BUY", []
    return "HOLD", []


def _avaliar_fundamentos(fund: dict, perfil: dict):
    """
    Retorna (sinal, motivos).
      SELL — fundamentos deteriorados (qualquer gatilho abaixo)
      BUY  — fundamentos aprovados pelos filtros da estratégia
      HOLD — nem deteriorado, nem aprovado
    O sinal BUY aqui é "elegível": o analisar_ativo ainda exige
    upside suficiente + tendência de alta para confirmar (exceto FIIs).
    """
    if perfil["estrategia"] == "FII":
        return _avaliar_fii(fund, perfil)

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
    # Dívida só é SELL quando ultrapassa o teto ESTRUTURAL do setor E há
    # deterioração real de lucro (queda de dois dígitos, não ruído). Alavancagem
    # alta mas estável (concessões reguladas) não é risco — no máximo mantém
    # fora do BUY (fica HOLD). -15% é a linha entre "flutuação" e "encolhimento".
    EPS_DETERIORACAO = -15
    teto_divida = perfil.get("divida_max")
    if (divida is not None and teto_divida is not None and divida > teto_divida
            and eps is not None and eps < EPS_DETERIORACAO):
        motivos.append(f"alavancagem {divida:.1f}x acima do teto setorial "
                       f"({teto_divida:.1f}x) com lucro em queda ({eps:.0f}%)")
    if motivos:
        return "SELL", motivos

    # ── Filtros de aprovação por estratégia ──────────────────────────────────
    teto_divida = perfil.get("divida_max")
    divida_ok   = divida is None or teto_divida is None or divida <= teto_divida
    roe_ok      = roe is not None and roe >= FILTRO_ROE_MIN * 100

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

def analisar_ativo(fund: dict, tec: dict, preco_compra: float = 0,
                   label_watchlist: str = None) -> dict:
    """
    Junta score + sinal + valuation + níveis técnicos num dict único,
    no formato consumido pelo main.py, console_alert e html_report.

    label_watchlist: perfil escolhido pelo usuário na watchlist (UI). Vale mais
    que o setor do Yahoo na resolução do perfil (ver resolver_perfil).

    Sinal BUY final exige as 3 condições (README):
      fundamentos aprovados + upside >= 10% + tendência de alta (MA50 > MA200).
    """
    tec = tec or {}
    ticker = fund.get("ticker", "")
    nome_perfil, perfil = resolver_perfil(ticker, fund.get("setor"), label_watchlist)

    score          = calcular_score(fund, perfil)
    sinal, motivos = _avaliar_fundamentos(fund, perfil)
    valuation      = calcular_valuation(fund, perfil)
    alertas        = list(motivos)

    # ── Confirmação do BUY: upside + tendência ────────────────────────────────
    # FIIs são avaliados por yield, não por preço-vs-justo (o DDM é circular
    # quando dy_alvo ≈ dy atual) — o sinal de _avaliar_fii já é final.
    tendencia_alta = tec.get("tendencia_alta")
    if sinal == "BUY" and perfil["estrategia"] != "FII":
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
