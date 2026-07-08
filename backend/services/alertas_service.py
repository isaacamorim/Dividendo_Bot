"""
backend/services/alertas_service.py — Geração de alertas do painel.

Chamado após salvar os snapshots do scan. Dois grupos:
  1. Mudança de sinal vs. dia anterior → NOVO_BUY / SAIU_BUY
  2. Posições da carteira vs. preço atual → STOP_LOSS / TAKE_PROFIT

Idempotente por dia: não duplica (ticker, tipo) no mesmo CURRENT_DATE.
Nunca levanta — o scan não pode falhar por causa de alerta.
"""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import func

from config.settings import STOP_LOSS_PCT, TAKE_PROFIT_PCT

from backend.models.alerta import Alerta
from backend.models.snapshot import Snapshot

logger = logging.getLogger("dividend_bot.alertas")


def _ja_existe_hoje(db, ticker: str, tipo: str) -> bool:
    return db.query(Alerta.id).filter(
        Alerta.ticker == ticker,
        Alerta.tipo == tipo,
        func.date(Alerta.created_at) == func.current_date(),
    ).first() is not None


def _inserir(db, ticker, tipo, mensagem, score=None, sinal=None) -> bool:
    if _ja_existe_hoje(db, ticker, tipo):
        return False
    db.add(Alerta(ticker=ticker, tipo=tipo, mensagem=mensagem, score=score, sinal=sinal))
    return True


def _detalhe(score, dy, upside) -> str:
    partes = []
    if score is not None:  partes.append(f"score {score:.1f}")
    if dy is not None:     partes.append(f"DY {dy:.1f}%")
    if upside is not None: partes.append(f"upside {upside:+.0f}%")
    return (" — " + ", ".join(partes)) if partes else ""


def _resumo_gpt(r: dict) -> str:
    """Anexa o resumo do GPT ao alerta NOVO_BUY (best-effort — vazio se falhar)."""
    try:
        from backend.services.gpt_analyst import analisar_ativo_gpt
        ana = analisar_ativo_gpt(r)
        if ana and ana.get("resumo"):
            return ". " + ana["resumo"]
    except Exception as e:                          # noqa: BLE001
        logger.warning("resumo GPT p/ alerta falhou (%s): %s", r.get("ticker"), e)
    return ""


def _sinal_anterior(db, ticker: str, dia: date):
    """Sinal do snapshot mais recente ANTES de 'dia' (o dia anterior de scan)."""
    row = (db.query(Snapshot.sinal)
             .filter(Snapshot.ticker == ticker, Snapshot.data < dia)
             .order_by(Snapshot.data.desc()).first())
    return row[0] if row else None


def _alertas_sinal(db, resultados, dia):
    for r in resultados:
        tk = r.get("ticker")
        hoje = r.get("sinal")
        if not tk or not hoje:
            continue
        ontem = _sinal_anterior(db, tk, dia)
        if ontem is None:            # primeiro registro do ticker → não alerta (evita spam)
            continue
        score = r.get("score")
        dy = (r.get("fundamentos") or {}).get("dy")
        upside = (r.get("valuation") or {}).get("upside")
        if ontem != "BUY" and hoje == "BUY":
            _inserir(db, tk, "NOVO_BUY",
                     f"{tk} entrou em BUY" + _detalhe(score, dy, upside) + _resumo_gpt(r),
                     score, hoje)
        elif ontem == "BUY" and hoje != "BUY":
            _inserir(db, tk, "SAIU_BUY", f"{tk} saiu de BUY (agora {hoje})" + _detalhe(score, dy, upside),
                     score, hoje)


def _alertas_carteira(db):
    # Import tardio: carteira_service puxa o core (portfolio/pandas) — evita custo/ciclo.
    from backend.services.carteira_service import resumo_carteira
    try:
        resumo = resumo_carteira(db)
    except Exception as e:                          # noqa: BLE001
        logger.warning("resumo_carteira p/ alertas falhou: %s", e)
        return
    for p in resumo.get("posicoes", []):
        pm = p.get("pm")
        atual = p.get("preco_atual")
        if not pm or not atual:
            continue
        var = atual / pm - 1
        if var <= STOP_LOSS_PCT:
            _inserir(db, p["ticker"], "STOP_LOSS",
                     f"{p['ticker']} atingiu STOP LOSS ({var * 100:+.1f}%) — "
                     f"PM R${pm:.2f}, atual R${atual:.2f}")
        elif var >= TAKE_PROFIT_PCT:
            _inserir(db, p["ticker"], "TAKE_PROFIT",
                     f"{p['ticker']} atingiu TAKE PROFIT ({var * 100:+.1f}%) — "
                     f"PM R${pm:.2f}, atual R${atual:.2f}")


def gerar_alertas(db, resultados: list, dia: date | None = None) -> None:
    """Gera os alertas do scan. Resiliente: loga e faz rollback se algo falhar."""
    dia = dia or date.today()
    try:
        _alertas_sinal(db, resultados, dia)
        _alertas_carteira(db)
        db.commit()
    except Exception as e:                          # noqa: BLE001
        logger.warning("gerar_alertas falhou: %s", e)
        db.rollback()
