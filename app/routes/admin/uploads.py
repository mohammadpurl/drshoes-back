from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.deps import get_admin_user
from app.models.user import User
from app.schemas.admin_product import MediaUploadResponse, UploadResponse
from app.services.storage_service import StorageService
from app.utils.slugify import slugify

router = APIRouter(prefix="/uploads")


@router.get("/suggest-slug")
async def suggest_slug(
    name: str = Query(..., min_length=1, max_length=255),
    _admin: User = Depends(get_admin_user),
):
    """پیشنهاد اسلاگ از روی نام محصول (قابل ویرایش در فرانت)."""
    return {"slug": slugify(name)}


@router.post("/media", response_model=MediaUploadResponse)
async def upload_product_media(
    file: UploadFile = File(...),
    slug: str | None = Query(
        None,
        description="اسلاگ محصول — فایل در پوشه products/{slug}/ ذخیره می‌شود",
    ),
    _admin: User = Depends(get_admin_user),
):
    """
    آپلود تصویر یا ویدئو. پاسخ شامل URL عمومی است؛ همان را در images/videos محصول بگذارید.
    """
    storage = StorageService(subfolder="products")
    result = await storage.save_media(file, slug=slug)
    return MediaUploadResponse(**result)


@router.post("/image", response_model=UploadResponse)
async def upload_product_image(
    file: UploadFile = File(...),
    slug: str | None = Query(None),
    _admin: User = Depends(get_admin_user),
):
    """سازگاری با نسخه قبل — فقط URL برمی‌گرداند."""
    storage = StorageService(subfolder="products")
    url = await storage.save_image(file, slug=slug)
    return UploadResponse(url=url)
