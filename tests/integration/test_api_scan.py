import os

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app

ADMIN_PW = os.getenv("ADMIN_PASSWORD", "220825")


def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_scan_latest_autenticado_nao_vazio():
    async with _client() as ac:
        await ac.post("/auth/login", json={"username": "isaac", "password": ADMIN_PW})
        r = await ac.get("/scan/latest")
        assert r.status_code == 200
        assert len(r.json()["resultados"]) > 0


@pytest.mark.asyncio
async def test_scan_historico_tem_serie():
    async with _client() as ac:
        await ac.post("/auth/login", json={"username": "isaac", "password": ADMIN_PW})
        r = await ac.get("/scan/historico/PETR4")
        assert r.status_code == 200
        assert "serie" in r.json()
