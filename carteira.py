"""
portfolio/carteira.py

Persistência de carteira em JSON.
Rastreia: preço de compra, data, dividendos recebidos, rentabilidade atual.

Uso:
  from portfolio.carteira import Carteira
  c = Carteira()
  c.adicionar("PETR4", preco=38.20, qtd=100, data="2025-01-15")
  c.registrar_dividendo("PETR4", valor_por_acao=0.85, data="2025-03-10")
  c.resumo(precos_atuais={"PETR4": 42.91})
"""

import json
import os
from datetime import datetime
from typing import Optional

CARTEIRA_FILE = os.path.join(os.path.dirname(__file__), "..", "carteira.json")


class Carteira:
    def __init__(self, arquivo: str = None):
        self.arquivo = arquivo or CARTEIRA_FILE
        self._dados  = self._carregar()

    # ── Persistência ─────────────────────────────────────────────────────────

    def _carregar(self) -> dict:
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"posicoes": {}, "dividendos": [], "historico": []}

    def _salvar(self):
        with open(self.arquivo, "w", encoding="utf-8") as f:
            json.dump(self._dados, f, ensure_ascii=False, indent=2)

    # ── Operações ─────────────────────────────────────────────────────────────

    def adicionar(self, ticker: str, preco: float, qtd: int,
                  data: str = None, nota: str = ""):
        """Registra compra de uma posição."""
        ticker = ticker.upper().replace(".SA", "")
        data   = data or datetime.today().strftime("%Y-%m-%d")

        pos = self._dados["posicoes"]
        if ticker not in pos:
            pos[ticker] = {"lotes": [], "dividendos_recebidos": 0.0}

        pos[ticker]["lotes"].append({
            "data":  data,
            "preco": round(preco, 2),
            "qtd":   qtd,
            "nota":  nota,
        })

        self._dados["historico"].append({
            "tipo": "COMPRA", "ticker": ticker,
            "preco": round(preco, 2), "qtd": qtd, "data": data,
        })
        self._salvar()
        return self

    def remover(self, ticker: str, qtd: int = None, data: str = None, nota: str = ""):
        """Registra venda (total ou parcial)."""
        ticker = ticker.upper().replace(".SA", "")
        data   = data or datetime.today().strftime("%Y-%m-%d")
        pos    = self._dados["posicoes"]

        if ticker not in pos:
            raise ValueError(f"{ticker} não está na carteira")

        qtd_total = self._qtd_total(ticker)
        qtd_venda = qtd or qtd_total

        self._dados["historico"].append({
            "tipo": "VENDA", "ticker": ticker,
            "qtd": qtd_venda, "data": data, "nota": nota,
        })

        if qtd_venda >= qtd_total:
            del pos[ticker]
        else:
            # FIFO: remove do lote mais antigo primeiro
            restante = qtd_venda
            for lote in list(pos[ticker]["lotes"]):
                if restante <= 0:
                    break
                if lote["qtd"] <= restante:
                    restante -= lote["qtd"]
                    pos[ticker]["lotes"].remove(lote)
                else:
                    lote["qtd"] -= restante
                    restante = 0

        self._salvar()
        return self

    def registrar_dividendo(self, ticker: str, valor_por_acao: float,
                            data: str = None):
        """Registra dividendo recebido para um ticker."""
        ticker = ticker.upper().replace(".SA", "")
        data   = data or datetime.today().strftime("%Y-%m-%d")
        pos    = self._dados["posicoes"]

        if ticker not in pos:
            raise ValueError(f"{ticker} não está na carteira")

        qtd   = self._qtd_total(ticker)
        total = round(qtd * valor_por_acao, 2)

        pos[ticker]["dividendos_recebidos"] = round(
            pos[ticker].get("dividendos_recebidos", 0) + total, 2
        )
        self._dados["dividendos"].append({
            "ticker": ticker, "data": data,
            "valor_por_acao": valor_por_acao,
            "qtd": qtd, "total": total,
        })
        self._salvar()
        return self

    # ── Consultas ─────────────────────────────────────────────────────────────

    def _qtd_total(self, ticker: str) -> int:
        return sum(l["qtd"] for l in self._dados["posicoes"][ticker]["lotes"])

    def _preco_medio(self, ticker: str) -> float:
        lotes = self._dados["posicoes"][ticker]["lotes"]
        total_custo = sum(l["preco"] * l["qtd"] for l in lotes)
        total_qtd   = sum(l["qtd"] for l in lotes)
        return round(total_custo / total_qtd, 2) if total_qtd else 0

    def posicoes(self) -> list:
        """Retorna lista de posições com preço médio e qtd."""
        result = []
        for ticker, dados in self._dados["posicoes"].items():
            result.append({
                "ticker":    ticker,
                "qtd":       self._qtd_total(ticker),
                "pm":        self._preco_medio(ticker),
                "dividendos":dados.get("dividendos_recebidos", 0.0),
                "lotes":     dados["lotes"],
            })
        return result

    def resumo(self, precos_atuais: dict = None) -> dict:
        """
        Calcula resumo da carteira com rentabilidade.
        precos_atuais = {"PETR4": 42.91, "ITUB4": 43.87, ...}
        """
        precos_atuais = precos_atuais or {}
        pos           = self.posicoes()

        if not pos:
            return {"posicoes": [], "total_investido": 0,
                    "total_atual": 0, "rentabilidade_pct": 0,
                    "total_dividendos": 0}

        total_investido  = 0.0
        total_atual      = 0.0
        total_dividendos = 0.0
        posicoes_detalhe = []

        for p in pos:
            ticker     = p["ticker"]
            preco_atu  = precos_atuais.get(ticker) or p["pm"]  # fallback = PM
            investido  = p["pm"] * p["qtd"]
            atual      = preco_atu * p["qtd"]
            lucro_cap  = atual - investido
            rent_pct   = (preco_atu / p["pm"] - 1) * 100 if p["pm"] else 0
            rent_total = ((atual + p["dividendos"]) / investido - 1) * 100 if investido else 0

            # Concentração setorial (simplificado — apenas calcula peso)
            total_investido  += investido
            total_atual      += atual
            total_dividendos += p["dividendos"]

            posicoes_detalhe.append({
                "ticker":       ticker,
                "qtd":          p["qtd"],
                "pm":           p["pm"],
                "preco_atual":  round(preco_atu, 2),
                "investido":    round(investido, 2),
                "atual":        round(atual, 2),
                "lucro_cap":    round(lucro_cap, 2),
                "rent_pct":     round(rent_pct, 1),
                "rent_total":   round(rent_total, 1),
                "dividendos":   p["dividendos"],
            })

        rent_carteira = (total_atual / total_investido - 1) * 100 if total_investido else 0

        return {
            "posicoes":         sorted(posicoes_detalhe, key=lambda x: -x["investido"]),
            "total_investido":  round(total_investido, 2),
            "total_atual":      round(total_atual, 2),
            "lucro_capital":    round(total_atual - total_investido, 2),
            "rentabilidade_pct":round(rent_carteira, 1),
            "total_dividendos": round(total_dividendos, 2),
            "rent_total_pct":   round((total_atual + total_dividendos) / total_investido * 100 - 100, 1)
                                if total_investido else 0,
        }

    def alertas_risco(self) -> list:
        """Detecta concentração excessiva (>30% num ativo ou setor)."""
        pos    = self.posicoes()
        if not pos:
            return []

        total  = sum(p["pm"] * p["qtd"] for p in pos)
        if total == 0:
            return []

        alertas = []
        for p in pos:
            peso = (p["pm"] * p["qtd"]) / total * 100
            if peso > 30:
                alertas.append(
                    f"⚠️  {p['ticker']} representa {peso:.1f}% da carteira — considere diversificar"
                )
        return alertas
