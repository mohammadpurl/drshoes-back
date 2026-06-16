from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_cart_token, get_current_user_optional
from app.database import get_db
from app.models.cart import Cart
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemRead, CartItemUpdate, CartRead
from app.schemas.product import ProductRead
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


def build_cart_response(cart, token: str | None = None) -> CartRead:
    subtotal, count = CartService.calc_subtotal(cart)
    items = []
    for item in cart.items:
        row = CartItemRead.model_validate(item)
        if item.product:
            row.product = ProductRead.model_validate(item.product)
        items.append(row)
    return CartRead(
        id=cart.id,
        cartToken=token or cart.session_token,
        items=items,
        itemCount=count,
        subtotal=subtotal,
    )


async def _resolve_cart(
    service: CartService,
    user: User | None,
    cart_token: str | None,
) -> tuple[Cart, str | None]:
    return await service.resolve_cart(user, cart_token)


@router.get("", response_model=CartRead)
async def get_cart(
    response: Response,
    user: User | None = Depends(get_current_user_optional),
    cart_token: str | None = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    cart, token = await _resolve_cart(service, user, cart_token)
    if token:
        response.headers["X-Cart-Token"] = token
    return build_cart_response(cart, token)


@router.post("/items", response_model=CartRead)
async def add_cart_item(
    body: CartItemCreate,
    response: Response,
    user: User | None = Depends(get_current_user_optional),
    cart_token: str | None = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    try:
        cart, token = await _resolve_cart(service, user, cart_token)
        cart = await service.add_item(cart, body)
        if token:
            response.headers["X-Cart-Token"] = token
        return build_cart_response(cart, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/items/{item_id}", response_model=CartRead)
async def update_cart_item(
    item_id: str,
    body: CartItemUpdate,
    response: Response,
    user: User | None = Depends(get_current_user_optional),
    cart_token: str | None = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    cart, token = await _resolve_cart(service, user, cart_token)
    if token:
        response.headers["X-Cart-Token"] = token

    updated = await service.update_item_quantity(cart, item_id, body.quantity)
    if not updated:
        raise HTTPException(status_code=404, detail="آیتم سبد یافت نشد")
    return build_cart_response(updated, token)


@router.delete("/items/{item_id}", response_model=CartRead)
async def remove_cart_item(
    item_id: str,
    response: Response,
    user: User | None = Depends(get_current_user_optional),
    cart_token: str | None = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    cart, token = await _resolve_cart(service, user, cart_token)
    if token:
        response.headers["X-Cart-Token"] = token

    updated = await service.remove_item(cart, item_id)
    if not updated:
        raise HTTPException(status_code=404, detail="آیتم سبد یافت نشد")
    return build_cart_response(updated, token)


@router.delete("", response_model=CartRead)
async def clear_cart(
    response: Response,
    user: User | None = Depends(get_current_user_optional),
    cart_token: str | None = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    cart, token = await _resolve_cart(service, user, cart_token)
    cart = await service.clear(cart)
    if token:
        response.headers["X-Cart-Token"] = token
    return build_cart_response(cart, token)
