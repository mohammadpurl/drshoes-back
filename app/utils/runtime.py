"""Runtime environment helpers."""
import os
from urllib.parse import urlparse


def is_serverless_runtime() -> bool:
    """True on Vercel / AWS Lambda (read-only filesystem under /var/task)."""
    return bool(
        os.environ.get("VERCEL")
        or os.environ.get("VERCEL_ENV")
        or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        or os.environ.get("AWS_EXECUTION_ENV")
    )


def is_local_database_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host in {"localhost", "127.0.0.1", "0.0.0.0", "host.docker.internal"}
