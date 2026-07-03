"""
backend/create_user.py — Cria o usuário admin a partir do .env, se não existir.
Idempotente. Rodar: python -m backend.create_user
"""

from backend.config import ADMIN_PASSWORD, ADMIN_USERNAME
from backend.db import SessionLocal
from backend.models.user import User
from backend.security import hash_senha


def main():
    if not ADMIN_PASSWORD or ADMIN_PASSWORD == "defina_uma_senha_aqui":
        raise SystemExit("ADMIN_PASSWORD nao definido no .env — abortando.")

    db = SessionLocal()
    try:
        existente = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if existente:
            print(f"usuario '{ADMIN_USERNAME}' ja existe (id {existente.id})")
            return
        novo = User(username=ADMIN_USERNAME, password_hash=hash_senha(ADMIN_PASSWORD))
        db.add(novo)
        db.commit()
        db.refresh(novo)
        print(f"usuario '{ADMIN_USERNAME}' criado (id {novo.id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
