"""Entry point for cPanel "Setup Python App" (Passenger).

Passenger looks for a module-level variable named `application`.
The 24/7 auto-send does NOT run here (shared hosting kills idle apps).
Use a cPanel Cron Job that runs `cron_auto_send.py` instead.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import app as application
from database import init_db

init_db()
