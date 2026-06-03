from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate
from app.services.address_service import AddressService

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("", response_model=list[AddressRead])
async def list_addresses(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AddressService(db)
    items = await service.list_for_user(user.id)
    return [AddressRead.model_validate(a) for a in items]


@router.post("", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
async def create_address(
    body: AddressCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AddressService(db)
    address = await service.create(user, body)
    return AddressRead.model_validate(address)


@router.patch("/{address_id}", response_model=AddressRead)
async def update_address(
    address_id: str,
    body: AddressUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AddressService(db)
    address = await service.update(user, address_id, body)
    if not address:
        raise HTTPException(status_code=404, detail="آدرس یافت نشد")
    return AddressRead.model_validate(address)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AddressService(db)
    ok = await service.delete(user, address_id)
    if not ok:
        raise HTTPException(status_code=404, detail="آدرس یافت نشد")
