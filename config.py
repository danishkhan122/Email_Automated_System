import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=True)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me-in-production")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

SMTP_SERVER = os.getenv("SMTP_SERVER", "mail.sprectexai.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_FROM = os.getenv("EMAIL_FROM", "shamaim@sprectexai.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

CC_RECEIVERS = [
    e.strip()
    for e in os.getenv(
        "CC_RECEIVERS",
        "osama@sprectexai.com,sales@sprectexai.com,danish.khan@sprectexai.com",
    ).split(",")
    if e.strip()
]

DAILY_EMAIL_LIMIT = int(os.getenv("DAILY_EMAIL_LIMIT", "20"))

AUTO_SEND_ENABLED = os.getenv("AUTO_SEND_ENABLED", "true").lower() in ("1", "true", "yes")
AUTO_SEND_INTERVAL_MINUTES = int(os.getenv("AUTO_SEND_INTERVAL_MINUTES", "30"))
AUTO_SEND_PER_RUN = int(os.getenv("AUTO_SEND_PER_RUN", "5"))
AUTO_SEND_EMAIL_DELAY_SECONDS = float(os.getenv("AUTO_SEND_EMAIL_DELAY_SECONDS", "3"))

# DATA_DIR can be overridden in production (e.g. a Render persistent disk
# mounted at /var/data) so the SQLite DB and uploads survive restarts.
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

DATABASE_PATH = DATA_DIR / "app.db"
UPLOADS_DIR = DATA_DIR / "uploads"
PROPOSALS_DIR = BASE_DIR / "proposals"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
