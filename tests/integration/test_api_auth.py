import os

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app

ADMIN_PW = os.getenv("ADMIN_PASSWORD", "220825")


def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_login_correto_retorna_token():
    async with _client() as ac:
        r = await ac.post("/auth/login", json={"username": "isaac", "password": ADMIN_PW})
        assert r.status_code == 200
        assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_login_errado_401():
    async with _client() as ac:
        r = await ac.post("/auth/login", json={"username": "isaac", "password": "errado"})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_scan_sem_token_401():
    async with _client() as ac:
        r = await ac.get("/scan/latest")
        assert r.status_code == 401
