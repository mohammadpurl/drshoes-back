from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.shop_config import PaymentInfoRead
from app.services.shop_config_service import ShopConfigService

router = APIRouter(tags=["payment"])


@router.get("/payment-info", response_model=PaymentInfoRead)
async def get_payment_info(db: AsyncSession = Depends(get_db)):
    """اطلاعات کارت برای پرداخت کارت‌به‌کارت (عمومی)."""
    config = await ShopConfigService(db).get()
    return PaymentInfoRead.model_validate(config)
