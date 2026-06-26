import logging
import threading
import time

from config import (
    AUTO_SEND_EMAIL_DELAY_SECONDS,
    AUTO_SEND_PER_RUN,
    DAILY_EMAIL_LIMIT,
)
from database import (
    conn_get_industry,
    count_pending_contacts,
    emails_sent_today,
    get_pending_contacts_queue,
    get_product,
    log_auto_send_run,
    mark_contact_failed,
    mark_contact_sent,
)
from email_service import _send_to_contact, log_email

logger = logging.getLogger("auto_sender")
_send_lock = threading.Lock()


def run_auto_send():
    """Send pending contacts automatically, respecting the daily limit."""
    if not _send_lock.acquire(blocking=False):
        msg = "Auto-send skipped: previous run still in progress."
        logger.info(msg)
        log_auto_send_run(0, 0, skipped=1, message=msg)
        return {"ok": True, "skipped": True, "sent": 0, "failed": 0, "message": msg}

    try:
        remaining_today = DAILY_EMAIL_LIMIT - emails_sent_today()
        if remaining_today <= 0:
            msg = f"Daily limit of {DAILY_EMAIL_LIMIT} emails reached."
            logger.info(msg)
            log_auto_send_run(0, 0, skipped=1, message=msg)
            return {"ok": True, "skipped": True, "sent": 0, "failed": 0, "message": msg}

        pending = count_pending_contacts()
        if pending <= 0:
            msg = "No pending contacts to send."
            logger.info(msg)
            log_auto_send_run(0, 0, skipped=1, message=msg)
            return {"ok": True, "skipped": True, "sent": 0, "failed": 0, "message": msg}

        batch_size = min(remaining_today, AUTO_SEND_PER_RUN, pending)
        contacts = get_pending_contacts_queue(batch_size)

        sent = 0
        failed = 0
        errors = []

        for contact in contacts:
            if emails_sent_today() >= DAILY_EMAIL_LIMIT:
                break

            product = get_product(contact["product_id"])
            industry = conn_get_industry(contact["industry_id"])
            if not product or not industry:
                mark_contact_failed(contact["id"])
                log_email(contact["id"], contact["product_id"], "failed", "Product or industry not found.")
                failed += 1
                errors.append(f"{contact['email']}: product/industry not found")
                continue

            try:
                _send_to_contact(contact, product, industry)
                mark_contact_sent(contact["id"])
                log_email(contact["id"], product["id"], "sent")
                sent += 1
                logger.info(
                    "Auto-sent to %s (%s) - %s / %s",
                    contact["email"],
                    contact["name"] or "no name",
                    product["name"],
                    industry["name"],
                )
            except Exception as exc:
                mark_contact_failed(contact["id"])
                log_email(contact["id"], product["id"], "failed", str(exc))
                failed += 1
                errors.append(f"{contact['email']}: {exc}")
                logger.error("Auto-send failed for %s: %s", contact["email"], exc)

            if sent + failed < batch_size and emails_sent_today() < DAILY_EMAIL_LIMIT:
                time.sleep(AUTO_SEND_EMAIL_DELAY_SECONDS)

        details = "\n".join(errors) if errors else ""
        msg = f"Auto-send complete: {sent} sent, {failed} failed."
        log_auto_send_run(sent, failed, message=msg, details=details)
        logger.info(msg)

        return {
            "ok": True,
            "sent": sent,
            "failed": failed,
            "remaining_today": max(0, DAILY_EMAIL_LIMIT - emails_sent_today()),
            "pending": count_pending_contacts(),
            "message": msg,
        }
    finally:
        _send_lock.release()
