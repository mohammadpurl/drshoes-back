from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_admin_user
from app.database import get_db
from app.models.user import User
from app.schemas.admin_product import ProductCreate, ProductUpdate
from app.schemas.product import ProductRead
from app.services.product_service import ProductService

router = APIRouter()


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    try:
        product = await service.create(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ProductRead.model_validate(product)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: str,
    body: ProductUpdate,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    try:
        product = await service.update(product_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not product:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")
    return ProductRead.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    ok = await service.delete(product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")
