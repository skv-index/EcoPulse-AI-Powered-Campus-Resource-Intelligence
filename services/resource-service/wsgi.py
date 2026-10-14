"""WSGI entry point for production servers.

Use:  gunicorn wsgi:app --bind 0.0.0.0:$PORT
(Named wsgi.py to avoid colliding with the app/ package.)
"""
from app import create_app

app = create_app()
