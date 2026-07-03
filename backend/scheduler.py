"""backend/scheduler.py — Scan automático diário via APScheduler (hora do .env, padrão 7h)."""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from backend.config import SCAN_HORA
from backend.db import SessionLocal
from backend.services.scanner import rodar_scan, salvar_snapshots

logger = logging.getLogger("dividend_bot.scheduler")


def job_scan_diario():
    logger.info("scan diario: iniciando")
    db = SessionLocal()
    try:
        n = salvar_snapshots(db, rodar_scan())
        logger.info("scan diario: %d snapshots salvos", n)
    except Exception as e:                          # noqa: BLE001
        logger.exception("scan diario falhou: %s", e)
    finally:
        db.close()


def iniciar_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="America/Sao_Paulo")
    sched.add_job(job_scan_diario, "cron", hour=SCAN_HORA, minute=0,
                  id="scan_diario", replace_existing=True)
    sched.start()
    logger.info("scheduler iniciado (scan diario %02dh00)", SCAN_HORA)
    return sched
