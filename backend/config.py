"""
backend/config.py — Configuração central lida do ambiente (.env).
Carrega o .env uma vez; todo módulo importa daqui em vez de reler os.getenv.
"""

import os

from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALG = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "isaac")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

SCAN_HORA = int(os.getenv("SCAN_HORA", "7"))
API_PORT = int(os.getenv("API_PORT", "8003"))
