from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_admin_user
from app.database import get_db
from app.models.user import User
from app.schemas.order import (
    AdminOrderListResponse,
    AdminOrderRead,
    OrderFulfillmentUpdate,
    OrderRead,
    OrderStatus,
    PaymentReviewRequest,
    PaymentStatus,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders")


def _admin_order_read(order, user: User | None = None) -> AdminOrderRead:
    data = OrderRead.model_validate(order).model_dump(by_alias=True)
    if user:
        data["username"] = user.username
        data["userFullName"] = user.full_name
        data["userPhone"] = user.phone
    return AdminOrderRead.model_validate({**data, "userId": order.user_id})


@router.get("", response_model=AdminOrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    status: OrderStatus | None = None,
    payment_status: PaymentStatus | None = Query(None, alias="paymentStatus"),
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    rows, total = await service.list_all(
        page=page,
        page_size=page_size,
        status=status.value if status else None,
        payment_status=payment_status.value if payment_status else None,
    )
    return AdminOrderListResponse(
        orders=[_admin_order_read(order, user) for order, user in rows],
        total=total,
    )


@router.get("/{order_id}", response_model=AdminOrderRead)
async def get_order(
    order_id: str,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.get_by_id_admin(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="سفارش یافت نشد")
    from sqlalchemy import select

    user = (
        await db.execute(select(User).where(User.id == order.user_id))
    ).scalar_one_or_none()
    return _admin_order_read(order, user)


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


@router.patch("/{order_id}/fulfillment", response_model=AdminOrderRead)
async def update_order_fulfillment(
    order_id: str,
    body: OrderFulfillmentUpdate,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.update_fulfillment(
        order_id,
        status=body.status,
        shipping_method=body.shippingMethod,
        tracking_number=body.trackingNumber,
        shipping_note=body.shippingNote,
    )
    if not order:
        raise HTTPException(status_code=404, detail="سفارش یافت نشد")
    from sqlalchemy import select

    user = (
        await db.execute(select(User).where(User.id == order.user_id))
    ).scalar_one_or_none()
    return _admin_order_read(order, user)


@router.patch("/{order_id}/payment", response_model=AdminOrderRead)
async def review_payment(
    order_id: str,
    body: PaymentReviewRequest,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    try:
        order = await service.review_payment(
            order_id,
            verify=body.action == "verify",
            note=body.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not order:
        raise HTTPException(status_code=404, detail="سفارش یافت نشد")
    from sqlalchemy import select

    user = (
        await db.execute(select(User).where(User.id == order.user_id))
    ).scalar_one_or_none()
    return _admin_order_read(order, user)
