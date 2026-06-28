"""Entry point for cPanel "Setup Python App" (Passenger).

Passenger looks for a module-level variable named `application`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import app as application
from database import init_db

init_db()
