"""
Test MinIO/S3 connection (run from Backend/ with venv active).

  python -m scripts.check_storage
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.services.storage_service import StorageService


async def main() -> None:
    print("STORAGE_BACKEND:", settings.storage_backend)
    if not settings.use_s3:
        print("Local mode — MinIO check skipped.")
        return

    storage = StorageService()
    try:
        client = storage._s3_client()
        await asyncio.to_thread(storage._ensure_bucket, client)
        client.head_bucket(Bucket=settings.s3_bucket_name)
        print("OK — bucket:", settings.s3_bucket_name)
        print("Endpoint:", settings.s3_endpoint_url)
        print("Public URL base:", settings.s3_public_url_base)
        print("\nNext: MinIO Console → bucket → Access Policy → public")
    except Exception as e:
        print("FAILED:", e)
        print("\n1. docker compose up -d minio")
        print("2. .env: S3_ENDPOINT_URL=http://127.0.0.1:9000")
        print("3. pip install boto3  (inside .venv)")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
