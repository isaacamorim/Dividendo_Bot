import os

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app

ADMIN_PW = os.getenv("ADMIN_PASSWORD", "220825")


def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_carteira_resumo():
    async with _client() as ac:
        await ac.post("/auth/login", json={"username": "isaac", "password": ADMIN_PW})
        r = await ac.get("/carteira")
        assert r.status_code == 200
        d = r.json()
        assert "posicoes" in d and "total_investido" in d


@pytest.mark.asyncio
async def test_carteira_crud_posicao_com_teardown():
    async with _client() as ac:
        await ac.post("/auth/login", json={"username": "isaac", "password": ADMIN_PW})

        # cria posição de teste
        criar = await ac.post("/carteira/posicao", json={
            "ticker": "TEST1", "preco_compra": 10.0, "quantidade": 5,
            "data_compra": "2026-01-10",
        })
        assert criar.status_code == 201
        pos_id = criar.json()["id"]

        # teardown: remove a posição de teste
        remover = await ac.delete(f"/carteira/posicao/{pos_id}")
        assert remover.status_code == 200
