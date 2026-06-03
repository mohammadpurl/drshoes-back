from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_admin_user
from app.database import get_db
from app.models.user import User
from app.schemas.order import OrderRead, OrderStatus
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders")


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: str,
    status: OrderStatus,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.update_status(order_id, status)
    if not order:
        raise HTTPException(status_code=404, detail="سفارش یافت نشد")
    return OrderRead.model_validate(order)
