from pathlib import Path

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

    # File uploads (local disk; swap base URL for CDN/S3 in production)
    upload_dir: Path = _BACKEND_ROOT / "uploads"
    static_url_base: str = "http://localhost:8000/static"
    max_upload_size_mb: int = 5
    allowed_image_types: str = "image/jpeg,image/png,image/webp"

    # Shop
    shipping_cost: int = 150_000
    free_shipping_min: int = 5_000_000

    # Seed admin
    admin_email: str = "admin@drshoes.local"
    admin_password: str = "admin123456"
    admin_full_name: str = "مدیر فروشگاه"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_image_mime_set(self) -> set[str]:
        return {m.strip() for m in self.allowed_image_types.split(",") if m.strip()}

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()
