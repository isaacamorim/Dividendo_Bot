"""
backend/routers/carteira.py — CRUD da carteira + resumo com rentabilidade (JWT).

GET    /carteira            resumo + posições com preço atual
POST   /carteira/posicao    cria posição
DELETE /carteira/posicao/{id}
POST   /carteira/dividendo  registra dividendo recebido
GET    /carteira/dividendos lista (filtro opcional por ticker)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.deps import usuario_atual
from backend.models.carteira import DividendoRecebido, Posicao
from backend.schemas.carteira import CarteiraResumo, DividendoCreate, PosicaoCreate
from backend.services.carteira_service import resumo_carteira

router = APIRouter(prefix="/carteira", tags=["carteira"], dependencies=[Depends(usuario_atual)])


def _limpo(ticker: str) -> str:
    return ticker.upper().replace(".SA", "")


@router.get("", response_model=CarteiraResumo)
def get_carteira(db: Session = Depends(get_db)):
    return resumo_carteira(db)


@router.post("/posicao", status_code=status.HTTP_201_CREATED)
def criar_posicao(dados: PosicaoCreate, db: Session = Depends(get_db)):
    p = Posicao(
        ticker=_limpo(dados.ticker), data_compra=dados.data_compra,
        preco_compra=dados.preco_compra, quantidade=dados.quantidade, nota=dados.nota,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "ticker": p.ticker, "quantidade": p.quantidade,
            "preco_compra": float(p.preco_compra), "data_compra": p.data_compra.isoformat()}


@router.delete("/posicao/{pos_id}")
def remover_posicao(pos_id: int, db: Session = Depends(get_db)):
    p = db.get(Posicao, pos_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Posicao nao encontrada")
    db.delete(p)
    db.commit()
    return {"status": "removida", "id": pos_id}


@router.post("/dividendo", status_code=status.HTTP_201_CREATED)
def registrar_dividendo(dados: DividendoCreate, db: Session = Depends(get_db)):
    tk = _limpo(dados.ticker)
    qtd = db.query(func.coalesce(func.sum(Posicao.quantidade), 0)).filter(Posicao.ticker == tk).scalar()
    total = round(qtd * dados.valor_por_acao, 2)
    d = DividendoRecebido(
        ticker=tk, data_pagamento=dados.data_pagamento,
        valor_por_acao=dados.valor_por_acao, quantidade=qtd, total=total,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return {"id": d.id, "ticker": tk, "valor_por_acao": float(d.valor_por_acao),
            "quantidade": qtd, "total": total}


@router.get("/dividendos")
def listar_dividendos(ticker: Optional[str] = Query(None), db: Session = Depends(get_db)):
    q = db.query(DividendoRecebido)
    if ticker:
        q = q.filter(DividendoRecebido.ticker == _limpo(ticker))
    rows = q.order_by(DividendoRecebido.data_pagamento.desc()).all()
    return [{"id": d.id, "ticker": d.ticker, "data_pagamento": d.data_pagamento.isoformat(),
             "valor_por_acao": float(d.valor_por_acao), "quantidade": d.quantidade,
             "total": float(d.total)} for d in rows]
