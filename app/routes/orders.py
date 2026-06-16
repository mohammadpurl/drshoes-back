from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_cart_token, get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.order import CheckoutRequest, OrderListResponse, OrderRead
from app.services.cart_service import CartService
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/checkout", response_model=OrderRead, status_code=201)
async def checkout(
    body: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart_service = CartService(db)
    cart = await cart_service.get_or_create_for_user(user)
    order_service = OrderService(db)
    try:
        order = await order_service.checkout(user, cart, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return OrderRead.model_validate(order)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50, alias="pageSize"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    orders, total = await service.list_for_user(user.id, page, page_size)
    return OrderListResponse(
        orders=[OrderRead.model_validate(o) for o in orders],
        total=total,
    )


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.get_by_id(user.id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="سفارش یافت نشد")
    return OrderRead.model_validate(order)


@router.post("/{order_id}/receipt", response_model=OrderRead)
async def upload_receipt(
    order_id: str,
    file: UploadFile = File(...),
    note: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    try:
        order = await service.upload_receipt(user.id, order_id, file, note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not order:
        raise HTTPException(status_code=404, detail="سفارش یافت نشد")
    return OrderRead.model_validate(order)
