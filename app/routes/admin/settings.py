from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_admin_user
from app.database import get_db
from app.models.user import User
from app.schemas.shop_config import PaymentInfoRead, PaymentInfoUpdate
from app.services.shop_config_service import ShopConfigService

router = APIRouter(prefix="/settings")


@router.get("/payment", response_model=PaymentInfoRead)
async def get_payment_settings(
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    config = await ShopConfigService(db).get()
    return PaymentInfoRead.model_validate(config)


@router.patch("/payment", response_model=PaymentInfoRead)
async def update_payment_settings(
    body: PaymentInfoUpdate,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    config = await ShopConfigService(db).update_payment(body)
    return PaymentInfoRead.model_validate(config)
