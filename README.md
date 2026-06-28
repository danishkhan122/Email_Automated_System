# Email Automated System

Flask-based admin dashboard for **Sprectex AI** to manage industry-specific cold email outreach. Upload contacts via CSV, auto-attach the right proposal, and send personalized HTML emails manually (individual, batch, or direct).

## Features

- **CSV upload** per product, industry, and country with day-wise upload history
- **3 products**: AI Recruiter System, Supply Chain Forecasting, Video Analytics Solution (with 14 sub-industries)
- **Personalized HTML emails** with logo, signature, and per-contact name/company
- **Auto-attached proposals** and demo video links based on product/industry
- **Send modes**: Individual, Batch, and Direct (manual recipient)
- **Email history** — day-wise log of all sent emails
- **Dashboard intelligence**: live industry/AI news feed and pitch suggestions
- **Daily limit** enforcement (configurable in `.env`)

## Tech Stack

- Python + Flask
- SQLite
- SMTP (SSL) for delivery

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
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

## CSV Format

Required column: `email`. Optional: `name`, `company`.

```csv
email,name,company
john@acme.com,John Doe,Acme Corp
```

## Deploy for your team (Render.com)

> Do NOT use Vercel. This app needs persistent storage (SQLite + file uploads).

1. Push to GitHub, then https://render.com -> **New +** -> **Blueprint** -> select repo.
2. Set `ADMIN_PASSWORD` and `EMAIL_PASSWORD` when prompted.
3. Share the Render URL with your team.

## Deploy on cPanel (subdomain)

Run on `mail.sprectexai.com` without touching your main site. Use **Setup Python App** with `passenger_wsgi.py` as the startup file.

## Note

The local database lives in `DATA_DIR` (or `data/` locally) and is git-ignored unless you commit `.env` for a private repo.
