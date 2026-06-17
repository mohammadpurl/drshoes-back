"""Runtime environment helpers."""
import os


def is_serverless_runtime() -> bool:
    """True on Vercel / AWS Lambda (read-only filesystem under /var/task)."""
    return bool(
        os.environ.get("VERCEL")
        or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        or os.environ.get("AWS_EXECUTION_ENV")
        or os.environ.get("VERCEL_ENV")
    )
