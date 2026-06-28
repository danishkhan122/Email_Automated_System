import smtplib
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    CC_RECEIVERS,
    DAILY_EMAIL_LIMIT,
    EMAIL_FROM,
    EMAIL_PASSWORD,
    SMTP_PORT,
    SMTP_SERVER,
)
from database import (
    conn_get_industry,
    emails_sent_today,
    get_contact,
    get_email_content,
    get_pending_contacts,
    get_product,
    log_direct_email,
    log_email,
    mark_contact_failed,
    mark_contact_sent,
)
from proposals_config import resolve_proposal_path
from email_templates import LOGO_PATH, build_email


def send_single_email(to_email, subject, html_body, plain_body, attachment=None):
    if not EMAIL_PASSWORD:
        raise ValueError("EMAIL_PASSWORD is not set in .env")

    message = MIMEMultipart("related")
    message["From"] = EMAIL_FROM
    message["To"] = to_email
    if CC_RECEIVERS:
        message["Cc"] = ", ".join(CC_RECEIVERS)
    message["Subject"] = subject

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(plain_body, "plain", "utf-8"))
    alt.attach(MIMEText(html_body, "html", "utf-8"))
    message.attach(alt)

    if LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as f:
            logo = MIMEImage(f.read())
        logo.add_header("Content-ID", "<sprectex_logo>")
        logo.add_header("Content-Disposition", "inline", filename="sprectex_logo.png")
        message.attach(logo)

    if attachment and attachment.exists():
        with open(attachment, "rb") as f:
            part = MIMEApplication(f.read(), Name=attachment.name)
        part["Content-Disposition"] = f'attachment; filename="{attachment.name}"'
        message.attach(part)

    recipients = [to_email] + CC_RECEIVERS
    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    try:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, recipients, message.as_string())
    finally:
        server.quit()


def _send_to_contact(contact, product, industry):
    email = build_email(
        contact["name"] or "",
        contact["company"] or "",
        industry["name"],
        product["slug"],
        industry["slug"],
    )
    attachment = resolve_proposal_path(product["slug"], industry["slug"])
    send_single_email(
        contact["email"],
        email["subject"],
        email["html"],
        email["plain"],
        attachment,
    )


def send_batch(product_id, industry_id, max_count=None):
    product = get_product(product_id)
    industry = conn_get_industry(industry_id)
    if not product or not industry:
        return {"ok": False, "error": "Product or industry not found.", "sent": 0, "failed": 0}

    remaining_today = DAILY_EMAIL_LIMIT - emails_sent_today()
    if remaining_today <= 0:
        return {
            "ok": False,
            "error": f"Daily limit of {DAILY_EMAIL_LIMIT} emails reached.",
            "sent": 0,
            "failed": 0,
        }

    batch_size = min(remaining_today, max_count or remaining_today)
    contacts = get_pending_contacts(product_id, industry_id, batch_size)

    sent = 0
    failed = 0
    errors = []

    for contact in contacts:
        if emails_sent_today() >= DAILY_EMAIL_LIMIT:
            break
        try:
            _send_to_contact(contact, product, industry)
            mark_contact_sent(contact["id"])
            log_email(contact["id"], product_id, "sent")
            sent += 1
        except Exception as exc:
            mark_contact_failed(contact["id"])
            log_email(contact["id"], product_id, "failed", str(exc))
            failed += 1
            errors.append(f"{contact['email']}: {exc}")

    return {
        "ok": True,
        "sent": sent,
        "failed": failed,
        "errors": errors,
        "remaining_today": max(0, DAILY_EMAIL_LIMIT - emails_sent_today()),
    }


def send_single_contact(contact_id):
    contact = get_contact(contact_id)
    if not contact:
        return {"ok": False, "error": "Contact not found."}

    if contact["status"] != "pending":
        return {"ok": False, "error": "This contact has already been emailed."}

    remaining_today = DAILY_EMAIL_LIMIT - emails_sent_today()
    if remaining_today <= 0:
        return {
            "ok": False,
            "error": f"Daily limit of {DAILY_EMAIL_LIMIT} emails reached.",
        }

    product = get_product(contact["product_id"])
    industry = conn_get_industry(contact["industry_id"])
    if not product or not industry:
        return {"ok": False, "error": "Product or industry not found."}

    try:
        _send_to_contact(contact, product, industry)
        mark_contact_sent(contact["id"])
        log_email(contact["id"], product["id"], "sent")
        return {
            "ok": True,
            "message": f"Email sent to {contact['name'] or contact['email']} ({contact['email']}).",
            "remaining_today": max(0, DAILY_EMAIL_LIMIT - emails_sent_today()),
        }
    except Exception as exc:
        mark_contact_failed(contact["id"])
        log_email(contact["id"], product["id"], "failed", str(exc))
        return {"ok": False, "error": str(exc)}


def send_direct_email(to_email, name, company, product_id, industry_id):
    to_email = (to_email or "").strip().lower()
    if not to_email or "@" not in to_email:
        return {"ok": False, "error": "Please enter a valid email address."}

    remaining_today = DAILY_EMAIL_LIMIT - emails_sent_today()
    if remaining_today <= 0:
        return {
            "ok": False,
            "error": f"Daily limit of {DAILY_EMAIL_LIMIT} emails reached.",
        }

    product = get_product(product_id)
    industry = conn_get_industry(industry_id)
    if not product or not industry:
        return {"ok": False, "error": "Product or industry not found."}

    email = build_email(
        name or "",
        company or "",
        industry["name"],
        product["slug"],
        industry["slug"],
    )
    attachment = resolve_proposal_path(product["slug"], industry["slug"])

    try:
        send_single_email(
            to_email,
            email["subject"],
            email["html"],
            email["plain"],
            attachment,
        )
        log_direct_email(product["id"], to_email, "sent", industry_id=industry["id"])
        display = name.strip() or to_email
        return {
            "ok": True,
            "message": f"Email sent directly to {display} ({to_email}).",
            "remaining_today": max(0, DAILY_EMAIL_LIMIT - emails_sent_today()),
        }
    except Exception as exc:
        log_direct_email(product["id"], to_email, "failed", industry_id=industry["id"], error_message=str(exc))
        return {"ok": False, "error": str(exc)}
