"""
backend/seed_carteira.py — Restaura a carteira de março (uma vez).
Idempotente: se já houver qualquer posição, não faz nada.
Rodar: python -m backend.seed_carteira
"""

from datetime import date

from sqlalchemy import func

from backend.db import SessionLocal
from backend.models.carteira import DividendoRecebido, Posicao

POSICOES = [
    # ticker, quantidade, preco_compra, data_compra
    ("BBAS3", 200, 25.10, date(2025, 1, 15)),
    ("PETR4", 100, 38.20, date(2025, 1, 15)),
    ("WEGE3", 50, 45.00, date(2025, 1, 15)),
]
DIVIDENDOS = [
    # ticker, valor_por_acao, data_pagamento
    ("PETR4", 0.85, date(2025, 3, 10)),
    ("BBAS3", 0.62, date(2025, 3, 10)),
]


def main():
    db = SessionLocal()
    try:
        if db.query(Posicao).count() > 0:
            print("carteira ja tem posicoes — nada a fazer (idempotente)")
            return

        for tk, qtd, preco, dt in POSICOES:
            db.add(Posicao(ticker=tk, quantidade=qtd, preco_compra=preco, data_compra=dt))
        db.flush()

        for tk, vpa, dt in DIVIDENDOS:
            qtd = db.query(func.coalesce(func.sum(Posicao.quantidade), 0)).filter(Posicao.ticker == tk).scalar()
            db.add(DividendoRecebido(ticker=tk, valor_por_acao=vpa, data_pagamento=dt,
                                     quantidade=qtd, total=round(qtd * vpa, 2)))
        db.commit()
        print("carteira de marco restaurada: 3 posicoes, 2 dividendos (total R$209,00)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
