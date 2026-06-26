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

## Deploy for your team (Render.com)

> Do NOT use Vercel. This app needs an always-on server (SQLite writes, file
> uploads, and the 24/7 background scheduler). Serverless platforms like Vercel
> crash because their filesystem is read-only and functions cannot run in the
> background.

### Steps

1. Push this repo to GitHub (already done).
2. Go to https://render.com and sign up (GitHub login).
3. Click **New +** -> **Blueprint**.
4. Select the `Email_Automated_System` repository. Render reads `render.yaml`.
5. When prompted, set the secret values:
   - `ADMIN_PASSWORD` (dashboard login for your team)
   - `EMAIL_PASSWORD` (the sender mailbox password)
6. Click **Apply**. Render builds and gives you a public URL like
   `https://sprectex-email-system.onrender.com`.
7. Share that URL + the `ADMIN_PASSWORD` with your team. Done.

### Plans
- **starter** (`$7/mo`, set in `render.yaml`): always-on + persistent disk, so
  contacts/history survive and the 24/7 auto-send keeps running. Recommended.
- **free**: good for testing, but the service sleeps when idle (pausing
  auto-send) and data resets on restart. Change `plan: starter` to `plan: free`
  in `render.yaml` to try it, and remove the `disk:` block (free has no disk).

## Deploy on your own cPanel (sprectexai.com) — without touching the existing site

Your existing website stays untouched. Run this app on a **subdomain** like
`mail.sprectexai.com` (it is login-protected, so it stays effectively private).

### Requirements
Your hosting must have cPanel's **"Setup Python App"** (Passenger). If you don't
see it in cPanel, ask your host to enable Python, or use Render instead.

### Steps
1. **Create a subdomain** in cPanel -> *Domains / Subdomains*, e.g.
   `mail.sprectexai.com`. Note its document root (e.g. `/home/USER/mail`).
2. **Upload the project** there (Git clone, or upload a zip and extract). Keep
   the existing site's folders separate — this only lives in the subdomain folder.
3. **cPanel -> Setup Python App -> Create Application**:
   - Python version: 3.10+ ; Application root: the subdomain folder ;
     Application URL: the subdomain ; Startup file: `passenger_wsgi.py` ;
     Entry point/Application object: `application`.
4. In that screen, **Run pip install** of `requirements.txt` (or use the given
   "Enter virtual environment" command, then `pip install -r requirements.txt`).
5. **Set environment variables** in the same screen (don't rely on `.env`):
   `ADMIN_PASSWORD`, `EMAIL_PASSWORD`, `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_FROM`,
   `CC_RECEIVERS`, `DAILY_EMAIL_LIMIT`, and `AUTO_SEND_ENABLED=false`.
6. **Restart** the app. Open `https://mail.sprectexai.com` and log in.

### 24/7 auto-send on cPanel = use a Cron Job (not the built-in scheduler)
Shared hosting pauses idle apps, so the background scheduler won't run reliably.
Instead, cPanel -> **Cron Jobs** -> add (every 30 minutes):

```
*/30 * * * * /home/USER/virtualenv/APPDIR/3.11/bin/python /home/USER/APPDIR/cron_auto_send.py >> /home/USER/APPDIR/cron.log 2>&1
```

Replace `USER`, `APPDIR`, and the Python version with the exact paths shown in
your "Setup Python App" screen (it lists the virtualenv path). The cron respects
`DAILY_EMAIL_LIMIT` and `AUTO_SEND_PER_RUN`, so still max 20/day.

## Run on local network (free alternative)

Run on one always-on PC and let the team access it over the same WiFi:

```bash
python app.py
```

Find that PC's local IP (`ipconfig` on Windows) and share
`http://<that-ip>:5000` with your team. The PC must stay on for 24/7 sending.

## Note

The app must stay running for the 24/7 auto-send scheduler to work. The local
database lives in `DATA_DIR` (a persistent disk on Render) and is git-ignored.
