"""
backend/services/gpt_analyst.py — Análise qualitativa de um ativo via GPT.

Recebe o dict de analisar_ativo() e devolve um parecer curto em JSON
(resumo, pontos_fortes, riscos, recomendacao, confianca). É best-effort:
qualquer falha (sem chave, timeout, JSON inválido) devolve None — o resto
do sistema segue sem GPT.

Cache em memória por (ticker, dia): não reanalisa o mesmo ativo no mesmo dia;
limpa sozinho na virada do dia.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import date
from typing import Optional

logger = logging.getLogger("dividend_bot.gpt")

_MODEL = "gpt-4o-mini"
_TIMEOUT = 15          # segundos
_MAX_TOKENS = 500
_TEMPERATURE = 0.3     # mais factual, menos criativo

_SYSTEM = (
    "Você é um analista de investimentos brasileiro especializado em ações da B3 "
    "e FIIs. Analise os dados fornecidos e responda APENAS em JSON válido, sem "
    "markdown, sem explicações fora do JSON. Seja direto e objetivo. Use português "
    "brasileiro. Foque em dividendos e valor de longo prazo."
)

# Cache simples em memória: {f"{ticker}_{iso}": parecer}
_cache: dict = {}
_cache_dia: Optional[date] = None


def _limpar_cache_se_novo_dia():
    global _cache_dia
    hoje = date.today()
    if _cache_dia != hoje:
        _cache.clear()
        _cache_dia = hoje


def _client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key, timeout=_TIMEOUT)
    except Exception as e:                          # noqa: BLE001
        logger.warning("nao consegui criar o client OpenAI: %s", e)
        return None


def _v(x, suf=""):
    return f"{x}{suf}" if x is not None else "N/D"


def _montar_prompt(r: dict) -> str:
    f = r.get("fundamentos", {}) or {}
    v = r.get("valuation", {}) or {}
    t = r.get("tecnico", {}) or {}

    tend = t.get("tendencia")
    if tend is None:
        ta = t.get("tendencia_alta")
        tend = "ALTA" if ta else ("BAIXA" if ta is False else "N/D")

    return f"""Ativo: {r.get('ticker', 'N/D')} ({r.get('setor_perfil', 'N/D')})
Estratégia: {r.get('estrategia', 'N/D')}

FUNDAMENTOS:
- Score: {_v(r.get('score'))}/10
- Sinal: {r.get('sinal', 'N/D')}
- DY: {_v(f.get('dy'), '%')}
- ROE: {_v(f.get('roe'), '%')}
- P/L: {_v(f.get('pl'))}
- P/VP: {_v(f.get('pvp'))}
- Payout: {_v(f.get('payout'), '%')}
- Dívida/EBITDA: {_v(f.get('divida_ebitda'), 'x')}
- EPS Growth: {_v(f.get('eps_growth'), '%')}
- Beta: {_v(f.get('beta'))}

VALUATION:
- Preço atual: R$ {_v(f.get('preco'))}
- Preço justo estimado: R$ {_v(v.get('preco_justo'))}
- Upside: {_v(v.get('upside'), '%')}
- Div. estimado: R$ {_v(v.get('div_estimado'))}/ano

TÉCNICO:
- MA200: R$ {_v(t.get('ma_longa'))}
- Momentum 12m: {_v(t.get('momentum_12m'), '%')}
- Tendência: {tend}

Retorne JSON com: resumo (2-3 frases), pontos_fortes (lista de até 3),
riscos (lista de até 3), recomendacao (1 frase), confianca ("alta"/"media"/"baixa")."""


def _extrair_json(texto: str):
    if not texto:
        return None
    try:
        return json.loads(texto)
    except Exception:
        pass
    m = re.search(r"\{.*\}", texto, re.DOTALL)     # tenta pescar o objeto no meio de texto
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def _normalizar(dados: dict) -> dict:
    def _lista(x):
        return [str(i) for i in x][:3] if isinstance(x, list) else []
    conf = str(dados.get("confianca", "media")).lower()
    if conf not in ("alta", "media", "baixa"):
        conf = "media"
    return {
        "resumo": str(dados.get("resumo", "")).strip(),
        "pontos_fortes": _lista(dados.get("pontos_fortes")),
        "riscos": _lista(dados.get("riscos")),
        "recomendacao": str(dados.get("recomendacao", "")).strip(),
        "confianca": conf,
    }


def analisar_ativo_gpt(resultado: dict) -> Optional[dict]:
    """Parecer do GPT para um ativo. Devolve None em qualquer falha."""
    ticker = (resultado.get("ticker") or "").upper()
    if not ticker:
        return None

    _limpar_cache_se_novo_dia()
    chave = f"{ticker}_{date.today().isoformat()}"
    if chave in _cache:
        return _cache[chave]

    client = _client()
    if client is None:
        logger.warning("GPT indisponivel (sem OPENAI_API_KEY ou SDK)")
        return None

    try:
        resp = client.chat.completions.create(
            model=_MODEL,
            temperature=_TEMPERATURE,
            max_tokens=_MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": _montar_prompt(resultado)},
            ],
        )
        conteudo = resp.choices[0].message.content
    except Exception as e:                          # noqa: BLE001
        logger.warning("chamada GPT falhou (%s): %s", ticker, e)
        return None

    dados = _extrair_json(conteudo or "")
    if not dados:
        logger.warning("GPT devolveu JSON invalido (%s)", ticker)
        return None

    parecer = _normalizar(dados)
    _cache[chave] = parecer
    return parecer
