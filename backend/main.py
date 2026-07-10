"""
backend/main.py — Entrypoint FastAPI do Dividend Bot.
Rodar: uvicorn backend.main:app --host 127.0.0.1 --port 8001
"""

from fastapi import FastAPI

from backend.routers import alertas, auth, backtest, carteira, scan, usuarios, watchlist

app = FastAPI(title="Dividend Bot API", version="1.0")

app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(carteira.router)
app.include_router(backtest.router)
app.include_router(alertas.router)
app.include_router(watchlist.router)
app.include_router(usuarios.router)


@app.on_event("startup")
def _startup():
    # Scheduler do scan diário sobe junto com a API.
    from backend.scheduler import iniciar_scheduler
    app.state.scheduler = iniciar_scheduler()


@app.get("/health")
def health():
    return {"status": "ok", "versao": "1.0"}
