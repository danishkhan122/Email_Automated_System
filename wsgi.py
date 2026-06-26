"""Production entry point used by gunicorn on Render.

Run with a SINGLE worker so only one auto-send scheduler exists:
    gunicorn wsgi:app --workers 1
"""
from app import app
from database import init_db
from scheduler import start_auto_sender

init_db()
start_auto_sender(app)

if __name__ == "__main__":
    app.run()
