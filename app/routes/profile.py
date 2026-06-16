from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    url = await StorageService(subfolder="avatars").save_avatar(file, user.id)
    service = AuthService(db)
    updated = await service.set_avatar(user, url)
    normalized = service.to_user_read(updated).avatar_url or url
    return {
        "avatar_url": normalized,
        "avatarUrl": normalized,
        "url": normalized,
    }


@router.delete("/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.clear_avatar(user)
