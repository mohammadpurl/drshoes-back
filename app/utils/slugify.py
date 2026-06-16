import re
import unicodedata


def slugify(text: str, max_length: int = 128) -> str:
    """Latin slug for URLs (Persian names → admin can edit suggested slug)."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    if not text:
        text = "product"
    return text[:max_length]
