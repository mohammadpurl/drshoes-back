from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.utils.runtime import is_serverless_runtime
from app.database import engine
from app.db_init import bootstrap_database
from app.routes import api_router
from app.services.storage_service import ensure_storage_ready


def _is_serverless_runtime() -> bool:
    return is_serverless_runtime()


def _ensure_local_media_dirs() -> None:
    """Create media folders for local dev only; never crash on read-only FS."""
    if settings.use_s3 or is_serverless_runtime():
        return
    try:
        settings.media_dir.mkdir(parents=True, exist_ok=True)
        (settings.media_dir / "products").mkdir(parents=True, exist_ok=True)
    except OSError:
        # e.g. Vercel /var/task is read-only even if VERCEL env is unset
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_local_media_dirs()
    await ensure_storage_ready()
    await bootstrap_database()
    yield
    await engine.dispose()


app = FastAPI(
    title="Dr.Shoes Running API",
    description="Backend API for Dr.Shoes Running store",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)

# Local static media — not available on Vercel serverless; use STORAGE_BACKEND=s3
if not settings.use_s3 and not _is_serverless_runtime():
    app.mount(
        "/static",
        StaticFiles(directory=settings.media_dir),
        name="static",
    )


@app.get("/")
async def root():
    return {
        "message": "Dr.Shoes Running API",
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
    }
