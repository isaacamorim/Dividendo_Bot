"""backend/models/user.py — Usuário + papel (espelha a tabela users)."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from backend.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(Text, nullable=False, default="leitor")   # admin|gestor|operador|leitor
    active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime(timezone=True))
    created_by = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
