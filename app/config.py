from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/drshoes"
    )
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    api_prefix: str = "/api/v1"
    page_size: int = 8
    debug: bool = True

    # Auth
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Data & media next to project (local now → S3 later via STORAGE_BACKEND=s3)
    data_dir: Path = _BACKEND_ROOT / "data"
    media_dir: Path = _BACKEND_ROOT / "media"

    # Storage: local = files under media/ | s3 = MinIO / AWS / Supabase S3 API
    storage_backend: Literal["local", "s3"] = "local"
    public_base_url: str = "http://localhost:8000"
    static_url_base: str = "http://localhost:8000/static"
    serve_media_via_api: bool = True

    s3_endpoint_url: str = "http://127.0.0.1:9000"
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_bucket_name: str = "drshoes-media"
    s3_region: str = "us-east-1"
    s3_public_url_base: str = "http://127.0.0.1:9000/drshoes-media"
    s3_auto_create_bucket: bool = True

    max_image_size_mb: int = 10
    max_video_size_mb: int = 50
    allowed_image_types: str = "image/jpeg,image/png,image/webp,image/gif"
    allowed_video_types: str = "video/mp4,video/webm,video/quicktime"

    # Shop
    shipping_cost: int = 150_000
    free_shipping_min: int = 5_000_000

    # Seed admin
    admin_username: str = "admin"
    admin_email: str | None = "admin@drshoes.local"
    admin_phone: str = "09000000000"
    admin_password: str = "admin123456"
    admin_full_name: str = "مدیر فروشگاه"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_image_mime_set(self) -> set[str]:
        return {m.strip() for m in self.allowed_image_types.split(",") if m.strip()}

    @property
    def allowed_video_mime_set(self) -> set[str]:
        return {m.strip() for m in self.allowed_video_types.split(",") if m.strip()}

    @property
    def max_image_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024

    @property
    def max_video_bytes(self) -> int:
        return self.max_video_size_mb * 1024 * 1024

    @property
    def use_s3(self) -> bool:
        return self.storage_backend == "s3"


settings = Settings()
