import atexit
import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from auto_sender import run_auto_send
from config import AUTO_SEND_ENABLED, AUTO_SEND_INTERVAL_MINUTES

logger = logging.getLogger("scheduler")
_scheduler = None


def start_auto_sender(app):
    global _scheduler

    if not AUTO_SEND_ENABLED:
        logger.info("Auto-send is disabled (AUTO_SEND_ENABLED=false).")
        return

    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        run_auto_send,
        "interval",
        minutes=AUTO_SEND_INTERVAL_MINUTES,
        id="auto_send_pending",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        run_auto_send,
        "date",
        run_date=datetime.now() + timedelta(seconds=20),
        id="auto_send_startup",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Auto-send scheduler started (every %s minutes).",
        AUTO_SEND_INTERVAL_MINUTES,
    )

    atexit.register(stop_auto_sender)


def stop_auto_sender():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Auto-send scheduler stopped.")
