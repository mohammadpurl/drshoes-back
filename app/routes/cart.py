from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_cart_token, get_current_user_optional
from app.database import get_db
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


@router.get("", response_model=CartRead)
async def get_cart(
    response: Response,
    user: User | None = Depends(get_current_user_optional),
    cart_token: str | None = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    if user:
        cart = await service.get_or_create_for_user(user)
        return build_cart_response(cart)

    cart, token = await service.get_or_create_guest(cart_token)
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
        if user:
            cart = await service.get_or_create_for_user(user)
            cart = await service.add_item(cart, body)
            return build_cart_response(cart)

        cart, token = await service.get_or_create_guest(cart_token)
        cart = await service.add_item(cart, body)
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
    if user:
        cart = await service.get_or_create_for_user(user)
    else:
        cart, token = await service.get_or_create_guest(cart_token)
        response.headers["X-Cart-Token"] = token

    updated = await service.update_item_quantity(cart, item_id, body.quantity)
    if not updated:
        raise HTTPException(status_code=404, detail="آیتم سبد یافت نشد")
    return build_cart_response(updated)


@router.delete("/items/{item_id}", response_model=CartRead)
async def remove_cart_item(
    item_id: str,
    response: Response,
    user: User | None = Depends(get_current_user_optional),
    cart_token: str | None = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    if user:
        cart = await service.get_or_create_for_user(user)
    else:
        cart, token = await service.get_or_create_guest(cart_token)
        response.headers["X-Cart-Token"] = token

    updated = await service.remove_item(cart, item_id)
    if not updated:
        raise HTTPException(status_code=404, detail="آیتم سبد یافت نشد")
    return build_cart_response(updated)


@router.delete("", response_model=CartRead)
async def clear_cart(
    response: Response,
    user: User | None = Depends(get_current_user_optional),
    cart_token: str | None = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    if user:
        cart = await service.get_or_create_for_user(user)
        cart = await service.clear(cart)
        return build_cart_response(cart)

    cart, token = await service.get_or_create_guest(cart_token)
    cart = await service.clear(cart)
    response.headers["X-Cart-Token"] = token
    return build_cart_response(cart, token)
