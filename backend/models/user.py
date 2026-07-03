"""backend/models/user.py — Usuário para autenticação simples (espelha a tabela users)."""

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from backend.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
