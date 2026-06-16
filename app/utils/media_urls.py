"""Build and normalize public media URLs for API responses."""

from app.config import settings


def _api_origin() -> str:
    return settings.public_base_url.rstrip("/")


def build_media_url(relative_key: str) -> str:
    """relative_key e.g. products/zoomfly6/abc.jpg"""
    key = relative_key.replace("\\", "/").lstrip("/")
    origin = _api_origin()

    if settings.use_s3:
        return f"{settings.s3_public_url_base.rstrip('/')}/{key}"

    if settings.serve_media_via_api:
        return f"{origin}{settings.api_prefix}/media/{key}"

    return f"{origin}/static/{key}"


def normalize_media_url(url: str) -> str:
    """Rewrite legacy /static/ URLs; leave external CDN URLs unchanged."""
    if not url:
        return url

    if url.startswith("http://") or url.startswith("https://"):
        static_marker = "/static/"
        api_marker = f"{settings.api_prefix}/media/"
        origin = _api_origin()

        if static_marker in url and settings.serve_media_via_api and not settings.use_s3:
            path = url.split(static_marker, 1)[1]
            return f"{origin}{settings.api_prefix}/media/{path.lstrip('/')}"

        if api_marker in url:
            path = url.split(api_marker, 1)[1]
            return f"{origin}{settings.api_prefix}/media/{path.lstrip('/')}"

        return url

    key = url.lstrip("/")
    if key.startswith("static/"):
        key = key[len("static/") :]
    return build_media_url(key)


def normalize_media_list(urls: list[str]) -> list[str]:
    return [normalize_media_url(u) for u in urls]
