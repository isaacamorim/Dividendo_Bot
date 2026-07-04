"""
data/validators.py — Sanity check centralizado de fundamentos.

Qualquer fonte (yfinance, brapi, cache antigo) passa pelo mesmo filtro antes
de virar decisão. Campo fora da faixa físico-econômica plausível vira None e
gera warning — melhor um buraco honesto que um número absurdo pontuando.
Preço não-positivo é erro: sem ele o ativo é inútil para o scanner.
"""

import logging

logger = logging.getLogger("dividend_bot.validators")

# Faixas plausíveis por campo (em pontos percentuais onde aplicável).
FAIXAS = {
    "dy":            (0, 40),      # %
    "roe":           (-200, 200),  # %
    "pl":            (0, 200),
    "lpa":           (-500, 500),
    "pvp":           (0, 50),
    "payout":        (0, 300),     # %
    "divida_ebitda": (0, 20),
}


def validar_fundamentos(dados: dict, ticker: str) -> dict:
    """Recebe dict bruto de qualquer fonte e devolve dict limpo.

    Campos fora da faixa viram None (com warning). Preço <= 0 ou ausente
    gera erro logado — o dado é inútil, mas não levantamos exceção para não
    derrubar o scan inteiro por um ativo ruim.
    """
    limpo = dict(dados)

    for campo, (minimo, maximo) in FAIXAS.items():
        valor = limpo.get(campo)
        if valor is None:
            continue
        try:
            v = float(valor)
        except (TypeError, ValueError):
            logger.warning("%s: %s não-numérico (%r) → descartado", ticker, campo, valor)
            limpo[campo] = None
            continue
        if not (minimo <= v <= maximo):
            logger.warning("%s: %s=%s fora de [%s, %s] → descartado",
                           ticker, campo, valor, minimo, maximo)
            limpo[campo] = None

    preco = limpo.get("preco")
    try:
        preco_ok = preco is not None and float(preco) > 0
    except (TypeError, ValueError):
        preco_ok = False
    if not preco_ok:
        # Sem preço válido o ativo é inútil — levanta (get_fundamentos já
        # retorna 'delisted' antes de chegar aqui quando não há preço).
        raise ValueError(f"{ticker}: preço inválido ({preco!r}) — dado inútil")

    return limpo
