"""Production entry point used by gunicorn on Render."""
from app import app
from database import init_db

init_db()

if __name__ == "__main__":
    app.run()
