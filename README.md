# Email Automated System

Flask-based admin dashboard for **Sprectex AI** to automate industry-specific cold email outreach. Upload contacts via CSV, auto-attach the right proposal, send personalized HTML emails, and let the built-in 24/7 scheduler send pending emails automatically.

## Features

- **CSV upload** per product, industry, and country with day-wise upload history
- **3 products**: AI Recruiter System, Supply Chain Forecasting, Video Analytics Solution (with 14 sub-industries)
- **Personalized HTML emails** with logo, signature, and per-contact name/company
- **Auto-attached proposals** based on the selected industry
- **Send modes**: Individual, Batch, and Direct (manual recipient)
- **24/7 auto-send** scheduler — sends pending contacts automatically, respecting a daily limit
- **Dashboard intelligence**: live industry/AI news feed and pitch suggestions
- **Daily limit** enforcement (default 20 emails/day)

## Tech Stack

- Python + Flask
- SQLite
- APScheduler (background auto-send)
- SMTP (SSL) for delivery

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env          # Windows (cp on macOS/Linux)
# then edit .env and set EMAIL_PASSWORD and other values

# 4. Run
python app.py
```

Open http://127.0.0.1:5000 and log in with `ADMIN_PASSWORD` from your `.env`.

## Configuration (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session secret | - |
| `ADMIN_PASSWORD` | Dashboard login password | `admin123` |
| `SMTP_SERVER` | SMTP host | `mail.sprectexai.com` |
| `SMTP_PORT` | SMTP SSL port | `465` |
| `EMAIL_FROM` | Sender address | - |
| `EMAIL_PASSWORD` | Sender mailbox password | - |
| `CC_RECEIVERS` | Comma-separated CC list | - |
| `DAILY_EMAIL_LIMIT` | Max emails per day | `20` |
| `AUTO_SEND_ENABLED` | Enable 24/7 auto-send | `true` |
| `AUTO_SEND_INTERVAL_MINUTES` | How often to check | `30` |
| `AUTO_SEND_PER_RUN` | Emails per run | `5` |
| `AUTO_SEND_EMAIL_DELAY_SECONDS` | Delay between emails | `3` |

## CSV Format

Required column: `email`. Optional: `name`, `company`.

```csv
email,name,company
john@acme.com,John Doe,Acme Corp
```

## Note

The app must stay running for the 24/7 auto-send scheduler to work. `.env` and the local database are git-ignored and never committed.
