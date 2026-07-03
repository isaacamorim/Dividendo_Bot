"""
backend/main.py — Entrypoint FastAPI do Dividend Bot.
Rodar: uvicorn backend.main:app --host 127.0.0.1 --port 8001
"""

from fastapi import FastAPI

from backend.routers import auth

app = FastAPI(title="Dividend Bot API", version="1.0")

app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}
