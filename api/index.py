"""Vercel entrypoint — re-export FastAPI app (ASGI native, no Mangum)."""
from app.main import app

__all__ = ["app"]
