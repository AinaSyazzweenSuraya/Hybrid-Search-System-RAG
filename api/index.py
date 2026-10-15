"""Vercel ASGI entrypoint. DATABASE_URL must point to persistent PostgreSQL."""
from app.main import app
