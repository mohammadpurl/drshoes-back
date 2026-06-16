from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter()


@router.get("/media/{file_path:path}")
async def serve_media(file_path: str):
    """Serve local product images/videos (same origin as API for frontend)."""
    if settings.use_s3:
        raise HTTPException(status_code=404, detail="Media is served from S3/CDN")

    safe = Path(file_path)
    if ".." in safe.parts:
        raise HTTPException(status_code=400, detail="Invalid path")

    full = (settings.media_dir / safe).resolve()
    media_root = settings.media_dir.resolve()
    if not str(full).startswith(str(media_root)) or not full.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(full)
