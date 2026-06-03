import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import settings

_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class StorageService:
    """Local disk storage. In production, upload to S3 and return CDN URLs."""

    def __init__(self, subfolder: str = "products"):
        self.subfolder = subfolder
        self.root = settings.upload_dir / subfolder
        self.root.mkdir(parents=True, exist_ok=True)

    def public_url(self, relative_path: str) -> str:
        base = settings.static_url_base.rstrip("/")
        rel = relative_path.replace("\\", "/").lstrip("/")
        return f"{base}/{rel}"

    async def save_image(self, file: UploadFile) -> str:
        if not file.content_type or file.content_type not in settings.allowed_image_mime_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="فرمت تصویر مجاز نیست (JPEG, PNG, WebP)",
            )

        data = await file.read()
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"حداکثر حجم فایل {settings.max_upload_size_mb} مگابایت است",
            )

        ext = _EXT_BY_MIME.get(file.content_type, ".bin")
        filename = f"{uuid.uuid4().hex}{ext}"
        dest = self.root / filename
        dest.write_bytes(data)

        relative = f"{self.subfolder}/{filename}"
        return self.public_url(relative)

    def delete_by_url(self, url: str) -> None:
        """Best-effort delete when URL points at our static base."""
        base = settings.static_url_base.rstrip("/")
        if not url.startswith(base):
            return
        rel = url[len(base) :].lstrip("/")
        path = settings.upload_dir / rel
        if path.is_file():
            path.unlink(missing_ok=True)
