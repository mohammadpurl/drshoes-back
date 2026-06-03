from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.cart import Cart
from app.models.order import Order, OrderItem
from app.models.user import User
from app.schemas.order import CheckoutRequest, OrderStatus
from app.services.address_service import AddressService
from app.services.cart_service import CartService
from app.utils.ids import new_id


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def checkout(self, user: User, cart: Cart, data: CheckoutRequest) -> Order:
        if not cart.items:
            raise ValueError("سبد خرید خالی است")

        address = await AddressService(self.db).get_for_user(user.id, data.address_id)
        if not address:
            raise ValueError("آدرس یافت نشد")

        subtotal, _ = CartService.calc_subtotal(cart)
        shipping = settings.shipping_cost
        if settings.free_shipping_min > 0 and subtotal >= settings.free_shipping_min:
            shipping = 0

        order = Order(
            id=new_id(),
            user_id=user.id,
            status=OrderStatus.pending.value,
            subtotal=subtotal,
            shipping_cost=shipping,
            total=subtotal + shipping,
            notes=data.notes,
            shipping_full_name=address.full_name,
            shipping_phone=address.phone,
            shipping_province=address.province,
            shipping_city=address.city,
            shipping_address=address.address_line,
            shipping_postal_code=address.postal_code,
        )
        self.db.add(order)

        for item in cart.items:
            if not item.product:
                continue
            unit = item.product.price
            line = unit * item.quantity
            image = item.product.images[0] if item.product.images else None
            self.db.add(
                OrderItem(
                    id=new_id(),
                    order_id=order.id,
                    product_id=item.product.id,
                    product_slug=item.product.slug,
                    product_name=item.product.name,
                    brand=item.product.brand,
                    image_url=image,
                    size=item.size,
                    quantity=item.quantity,
                    unit_price=unit,
                    line_total=line,
                )
            )

        await CartService(self.db).clear(cart)
        await self.db.commit()

        return await self.get_by_id(user.id, order.id)  # type: ignore[return-value]

    async def get_by_id(self, user_id: str, order_id: str) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id, Order.user_id == user_id)
            .options(selectinload(Order.items))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Order], int]:
        base = select(Order).where(Order.user_id == user_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            base.options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def update_status(self, order_id: str, status: OrderStatus) -> Order | None:
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            return None
        order.status = status.value
        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_by_id(order.user_id, order.id)
