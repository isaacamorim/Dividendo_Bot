"""
data/cache.py — Cache local de fundamentos com shelve (stdlib, zero deps).

Guarda cada ticker como {"dados": dict, "expira_em": epoch}. A expiração é
decidida na escrita (TTL passado em set), então o mesmo cache serve dados com
validades diferentes. Abre/fecha o shelve a cada operação e serializa com um
Lock — evita handles pendurados e corrupção sob acesso concorrente.

TTLs padrão: 4h para preços, 24h para fundamentos.
Arquivo: .cache/fundamentals (ignorado pelo git).
"""

from __future__ import annotations  # compat Python 3.8 (VPS) — annotations lazy

import os
import shelve
import threading
import time

TTL_PRECOS_H = 4.0        # preços mudam ao longo do pregão
TTL_FUNDAMENTOS_H = 24.0  # DY/ROE/LPA mudam a cada balanço, não a cada hora

_CAMINHO_PADRAO = os.path.join(".cache", "fundamentals")


class Cache:
    def __init__(self, caminho: str = _CAMINHO_PADRAO):
        self._caminho = caminho
        self._lock = threading.Lock()
        pasta = os.path.dirname(caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)

    def get(self, ticker: str) -> dict | None:
        """Retorna os dados se houver hit não-expirado, senão None."""
        chave = ticker.upper()
        with self._lock:
            try:
                with shelve.open(self._caminho, flag="c", writeback=False) as db:
                    reg = db.get(chave)
            except Exception:
                return None
        if not reg or time.time() >= reg.get("expira_em", 0):
            return None
        return reg["dados"]

    def set(self, ticker: str, dados: dict, ttl_horas: float = TTL_FUNDAMENTOS_H):
        """Grava os dados com validade de ttl_horas a partir de agora."""
        chave = ticker.upper()
        reg = {"dados": dados, "expira_em": time.time() + ttl_horas * 3600}
        with self._lock:
            try:
                with shelve.open(self._caminho, flag="c", writeback=False) as db:
                    db[chave] = reg
            except Exception:
                pass  # cache é otimização, nunca deve quebrar o fluxo

    def invalidar(self, ticker: str):
        """Remove uma entrada (força refetch na próxima chamada)."""
        chave = ticker.upper()
        with self._lock:
            try:
                with shelve.open(self._caminho, flag="c", writeback=False) as db:
                    if chave in db:
                        del db[chave]
            except Exception:
                pass

    def limpar_expirados(self) -> int:
        """Varre e remove entradas vencidas. Retorna quantas removeu."""
        agora = time.time()
        with self._lock:
            try:
                with shelve.open(self._caminho, flag="c", writeback=False) as db:
                    vencidos = [k for k, v in db.items()
                                if agora >= v.get("expira_em", 0)]
                    for k in vencidos:
                        del db[k]
            except Exception:
                return 0
        return len(vencidos)


# Instância compartilhada do módulo
cache = Cache()
