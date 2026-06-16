"""
Upload local media/ files to S3 and update product URLs in the database.

Prerequisites:
  - .env: STORAGE_BACKEND=s3 + valid S3_* credentials
  - pip install boto3

Usage (from Backend/):
  python -m scripts.migrate_media_to_s3
  python -m scripts.migrate_media_to_s3 --dry-run
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.product import Product
from app.services.storage_service import StorageService

_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
}


def _local_prefix() -> str:
    return settings.static_url_base.rstrip("/") + "/"


def _collect_local_files() -> list[tuple[Path, str]]:
    """Return (file_path, object_key relative to media_dir)."""
    root = settings.media_dir
    if not root.is_dir():
        return []
    out: list[tuple[Path, str]] = []
    for path in root.rglob("*"):
        if path.is_file() and path.name != ".gitkeep":
            key = path.relative_to(root).as_posix()
            out.append((path, key))
    return out


async def migrate(*, dry_run: bool) -> None:
    if not settings.use_s3:
        print("Set STORAGE_BACKEND=s3 in .env before migrating.")
        sys.exit(1)

    storage = StorageService()
    local_base = _local_prefix()
    files = _collect_local_files()
    if not files:
        print("No files under", settings.media_dir)
        return

    url_map: dict[str, str] = {}

    for path, key in files:
        new_url = storage.public_url(key)
        old_url = local_base + key
        url_map[old_url] = new_url
        if dry_run:
            print(f"[dry-run] {key} -> {new_url}")
            continue
        content_type = _MIME.get(path.suffix.lower(), "application/octet-stream")
        data = path.read_bytes()
        await asyncio.to_thread(storage._upload_s3, key, data, content_type)
        print(f"Uploaded: {key}")

    if dry_run:
        print(f"\nWould upload {len(files)} file(s). Run without --dry-run to apply.")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product))
        products = list(result.scalars().all())
        updated = 0
        for product in products:
            changed = False
            new_images = [
                url_map.get(u, u) for u in (product.images or [])
            ]
            new_videos = [
                url_map.get(u, u) for u in (product.videos or [])
            ]
            if new_images != product.images:
                product.images = new_images
                changed = True
            if new_videos != product.videos:
                product.videos = new_videos
                changed = True
            if changed:
                updated += 1
        await session.commit()
        print(f"Updated {updated} product(s) in database.")

    print("Done. New uploads use S3 automatically.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(migrate(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
