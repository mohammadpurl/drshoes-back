import asyncio
import logging
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.utils.media_urls import build_media_url
from app.utils.runtime import is_serverless_runtime

logger = logging.getLogger(__name__)

_EXT_BY_MIME: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "application/pdf": ".pdf",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}

_MAX_AVATAR_BYTES = 2 * 1024 * 1024
_AVATAR_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_RECEIPT_MIMES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
_MAX_RECEIPT_BYTES = 5 * 1024 * 1024


def _media_kind(content_type: str) -> str:
    if content_type in settings.allowed_image_mime_set:
        return "image"
    if content_type in settings.allowed_video_mime_set:
        return "video"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="فرمت مجاز: تصویر (JPEG, PNG, WebP, GIF) یا ویدئو (MP4, WebM, MOV)",
    )


def _max_bytes(kind: str) -> int:
    return settings.max_video_bytes if kind == "video" else settings.max_image_bytes


class StorageService:
    """Upload product media to S3-compatible storage (MinIO / AWS) or local disk."""

    def __init__(self, subfolder: str = "products"):
        self.subfolder = subfolder

    def _object_key(self, filename: str, slug: str | None) -> str:
        if slug:
            safe = slugify_path_segment(slug)
            return f"{self.subfolder}/{safe}/{filename}"
        return f"{self.subfolder}/{filename}"

    def public_url(self, object_key: str) -> str:
        return build_media_url(object_key)

    async def save_media(self, file: UploadFile, slug: str | None = None) -> dict:
        if not file.content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="نوع فایل مشخص نیست",
            )

        kind = _media_kind(file.content_type)
        data = await file.read()
        limit = _max_bytes(kind)
        if len(data) > limit:
            mb = limit // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"حداکثر حجم {kind} برابر {mb} مگابایت است",
            )

        ext = _EXT_BY_MIME.get(file.content_type, ".bin")
        filename = f"{uuid.uuid4().hex}{ext}"
        key = self._object_key(filename, slug)

        try:
            if settings.use_s3:
                await asyncio.to_thread(self._upload_s3, key, data, file.content_type)
            else:
                await asyncio.to_thread(self._upload_local, key, data)
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            ) from e

        return {
            "url": self.public_url(key),
            "key": key,
            "kind": kind,
            "contentType": file.content_type,
        }

    def _upload_local(self, key: str, data: bytes) -> None:
        if is_serverless_runtime():
            raise RuntimeError(
                "آپلود فایل روی Vercel ممکن نیست. تصاویر را در media/products "
                "قرار دهید و commit کنید، یا STORAGE_BACKEND=s3 تنظیم کنید."
            )
        path = settings.media_dir / key
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        except OSError as e:
            raise RuntimeError(
                "ذخیرهٔ محلی فایل ممکن نیست (دیسک فقط خواندنی). "
                "از S3 یا قرار دادن فایل در media/products استفاده کنید."
            ) from e

    def _s3_client(self):
        try:
            import boto3
            from botocore.client import Config
        except ImportError as e:
            raise RuntimeError(
                "boto3 نصب نیست. در venv پروژه: pip install boto3"
            ) from e
        return boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def _ensure_bucket(self, client) -> None:
        from botocore.exceptions import ClientError

        if not settings.s3_auto_create_bucket:
            return
        try:
            client.head_bucket(Bucket=settings.s3_bucket_name)
        except ClientError:
            try:
                client.create_bucket(Bucket=settings.s3_bucket_name)
                logger.info("Created S3 bucket: %s", settings.s3_bucket_name)
            except ClientError as e:
                logger.warning("Could not create bucket: %s", e)

    def _upload_s3(self, key: str, data: bytes, content_type: str) -> None:
        client = self._s3_client()
        self._ensure_bucket(client)
        client.upload_fileobj(
            BytesIO(data),
            settings.s3_bucket_name,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    async def save_image(self, file: UploadFile, slug: str | None = None) -> str:
        """Backward-compatible: returns URL only."""
        result = await self.save_media(file, slug=slug)
        return result["url"]

    async def save_avatar(self, file: UploadFile, user_id: str) -> str:
        if not file.content_type or file.content_type not in _AVATAR_MIMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="فرمت مجاز آواتار: JPEG, PNG, WebP یا GIF",
            )
        data = await file.read()
        if len(data) > _MAX_AVATAR_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="حداکثر حجم تصویر آواتار ۲ مگابایت است",
            )
        ext = _EXT_BY_MIME.get(file.content_type, ".bin")
        filename = f"{uuid.uuid4().hex}{ext}"
        key = f"avatars/{slugify_path_segment(user_id)}/{filename}"

        try:
            if settings.use_s3:
                await asyncio.to_thread(
                    self._upload_s3, key, data, file.content_type
                )
            else:
                await asyncio.to_thread(self._upload_local, key, data)
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            ) from e

        return self.public_url(key)

    async def save_receipt(self, file: UploadFile, order_id: str) -> str:
        if not file.content_type or file.content_type not in _RECEIPT_MIMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="فرمت مجاز رسید: JPEG, PNG, WebP یا PDF",
            )
        data = await file.read()
        if len(data) > _MAX_RECEIPT_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="حداکثر حجم رسید ۵ مگابایت است",
            )
        ext = _EXT_BY_MIME.get(file.content_type, ".bin")
        filename = f"{uuid.uuid4().hex}{ext}"
        key = f"receipts/{slugify_path_segment(order_id)}/{filename}"

        try:
            if settings.use_s3:
                await asyncio.to_thread(
                    self._upload_s3, key, data, file.content_type
                )
            else:
                await asyncio.to_thread(self._upload_local, key, data)
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
            ) from e

        return self.public_url(key)


def slugify_path_segment(slug: str) -> str:
    import re

    s = slug.strip().lower()
    s = re.sub(r"[^a-z0-9\-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "item"


async def ensure_storage_ready() -> None:
    """Called on startup when using S3/MinIO."""
    if not settings.use_s3:
        logger.info("Storage: local disk (%s)", settings.media_dir)
        return
    try:
        client = StorageService()._s3_client()
        await asyncio.to_thread(StorageService()._ensure_bucket, client)
        logger.info(
            "Storage: S3/MinIO OK — bucket=%s endpoint=%s",
            settings.s3_bucket_name,
            settings.s3_endpoint_url,
        )
    except RuntimeError as e:
        logger.error("Storage: %s", e)
    except Exception as e:
        logger.warning(
            "Storage: MinIO در دسترس نیست (%s). docker compose up -d minio",
            e,
        )
