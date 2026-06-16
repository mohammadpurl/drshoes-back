from datetime import UTC, datetime

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.cart import Cart
from app.models.order import Order, OrderItem
from app.models.user import User
from app.schemas.order import CheckoutRequest, OrderStatus, PaymentStatus
from app.services.address_service import AddressService
from app.services.cart_service import CartService
from app.services.storage_service import StorageService
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
            payment_status=PaymentStatus.awaiting_receipt.value,
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

    async def upload_receipt(
        self,
        user_id: str,
        order_id: str,
        file: UploadFile,
        note: str | None = None,
    ) -> Order | None:
        order = await self.get_by_id(user_id, order_id)
        if not order:
            return None
        if order.status == OrderStatus.cancelled.value:
            raise ValueError("سفارش لغو شده است")
        if order.payment_status == PaymentStatus.verified.value:
            raise ValueError("پرداخت این سفارش قبلاً تأیید شده است")

        url = await StorageService(subfolder="receipts").save_receipt(file, order_id)
        order.receipt_url = url
        order.receipt_note = note
        order.receipt_uploaded_at = datetime.now(UTC)
        order.payment_status = PaymentStatus.pending_review.value
        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_by_id(user_id, order_id)

    async def review_payment(
        self,
        order_id: str,
        *,
        verify: bool,
        note: str | None = None,
    ) -> Order | None:
        order = await self.get_by_id_admin(order_id)
        if not order:
            return None
        if order.payment_status not in (
            PaymentStatus.pending_review.value,
            PaymentStatus.rejected.value,
        ) and not (verify and order.receipt_url):
            raise ValueError("رسید پرداخت برای بررسی موجود نیست")

        if verify:
            order.payment_status = PaymentStatus.verified.value
            if order.status == OrderStatus.pending.value:
                order.status = OrderStatus.confirmed.value
            order.payment_review_note = note
        else:
            order.payment_status = PaymentStatus.rejected.value
            order.payment_review_note = note or "رسید پرداخت تأیید نشد"

        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_by_id_admin(order_id)

    async def get_by_id(self, user_id: str, order_id: str) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id, Order.user_id == user_id)
            .options(selectinload(Order.items))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_admin(self, order_id: str) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
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

    async def list_all(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        payment_status: str | None = None,
    ) -> tuple[list[tuple[Order, User]], int]:
        base = select(Order, User).join(User, Order.user_id == User.id)
        if status:
            base = base.where(Order.status == status)
        if payment_status:
            base = base.where(Order.payment_status == payment_status)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            base.options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        rows = [(order, user) for order, user in result.all()]
        return rows, total

    async def update_status(self, order_id: str, status: OrderStatus) -> Order | None:
        order = await self.get_by_id_admin(order_id)
        if not order:
            return None
        order.status = status.value
        if status == OrderStatus.shipped and not order.shipped_at:
            order.shipped_at = datetime.now(UTC)
        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_by_id_admin(order_id)

    async def update_fulfillment(
        self,
        order_id: str,
        *,
        status: OrderStatus | None = None,
        shipping_method: str | None = None,
        tracking_number: str | None = None,
        shipping_note: str | None = None,
    ) -> Order | None:
        order = await self.get_by_id_admin(order_id)
        if not order:
            return None

        if status is not None:
            order.status = status.value
            if status == OrderStatus.shipped and not order.shipped_at:
                order.shipped_at = datetime.now(UTC)

        if shipping_method is not None:
            order.shipping_method = shipping_method.strip() or None
        if tracking_number is not None:
            order.tracking_number = tracking_number.strip() or None
        if shipping_note is not None:
            order.shipping_note = shipping_note.strip() or None

        order.updated_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get_by_id_admin(order_id)
