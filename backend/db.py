"""
backend/db.py — Conexão PostgreSQL via SQLAlchemy 2.0.

DATABASE_URL vem do ambiente (.env), nunca hardcoded. Engine com pool_pre_ping
para não morrer em conexão ociosa. Base/SessionLocal reusados por models e routers.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não definido. Copie .env.example para .env e preencha."
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """Dependency do FastAPI: cede uma sessão e fecha ao fim."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def checar_conexao() -> str:
    """Testa a conexão e retorna 'usuario@banco'. Levanta se falhar."""
    with engine.connect() as conn:
        row = conn.execute(text("SELECT current_user, current_database()")).one()
    return f"{row[0]}@{row[1]}"
