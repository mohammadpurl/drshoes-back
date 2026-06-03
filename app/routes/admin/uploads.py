from fastapi import APIRouter, Depends, File, UploadFile

from app.core.deps import get_admin_user
from app.models.user import User
from app.schemas.admin_product import UploadResponse
from app.services.storage_service import StorageService

router = APIRouter(prefix="/uploads")


@router.post("/image", response_model=UploadResponse)
async def upload_product_image(
    file: UploadFile = File(...),
    _admin: User = Depends(get_admin_user),
):
    storage = StorageService(subfolder="products")
    url = await storage.save_image(file)
    return UploadResponse(url=url)
