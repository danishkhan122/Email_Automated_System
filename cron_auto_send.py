"""Run ONE auto-send batch. Designed to be called by a cPanel Cron Job.

Example cron (every 30 minutes), adjust the paths to your hosting:
    */30 * * * * /home/USER/virtualenv/APPDIR/3.11/bin/python /home/USER/APPDIR/cron_auto_send.py >> /home/USER/APPDIR/cron.log 2>&1

Each run respects DAILY_EMAIL_LIMIT and AUTO_SEND_PER_RUN from your .env.
"""
import sys
from datetime import datetime

from database import init_db
from auto_sender import run_auto_send

if __name__ == "__main__":
    init_db()
    result = run_auto_send()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] auto-send: {result}")
    sys.exit(0)
