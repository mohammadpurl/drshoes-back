from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import PaymentStatus


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def summary(self) -> dict:
        total_orders = (
            await self.db.execute(select(func.count()).select_from(Order))
        ).scalar_one()

        total_revenue = (
            await self.db.execute(
                select(func.coalesce(func.sum(Order.total), 0)).where(
                    Order.payment_status == PaymentStatus.verified.value
                )
            )
        ).scalar_one()

        pending_payments = (
            await self.db.execute(
                select(func.count()).select_from(Order).where(
                    Order.payment_status == PaymentStatus.pending_review.value
                )
            )
        ).scalar_one()

        awaiting_receipt = (
            await self.db.execute(
                select(func.count()).select_from(Order).where(
                    Order.payment_status == PaymentStatus.awaiting_receipt.value
                )
            )
        ).scalar_one()

        verified_payments = (
            await self.db.execute(
                select(func.count()).select_from(Order).where(
                    Order.payment_status == PaymentStatus.verified.value
                )
            )
        ).scalar_one()

        confirmed_orders = (
            await self.db.execute(
                select(func.count()).select_from(Order).where(
                    Order.status.in_(["confirmed", "shipped", "delivered"])
                )
            )
        ).scalar_one()

        return {
            "total_orders": int(total_orders or 0),
            "total_revenue": int(total_revenue or 0),
            "pending_payments": int(pending_payments or 0),
            "awaiting_receipt": int(awaiting_receipt or 0),
            "verified_payments": int(verified_payments or 0),
            "confirmed_orders": int(confirmed_orders or 0),
        }

    async def by_brand(self, limit: int = 20) -> list[dict]:
        stmt = (
            select(
                OrderItem.brand,
                func.count(func.distinct(OrderItem.order_id)).label("order_count"),
                func.sum(OrderItem.quantity).label("quantity"),
                func.sum(OrderItem.line_total).label("revenue"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.payment_status == PaymentStatus.verified.value)
            .group_by(OrderItem.brand)
            .order_by(func.sum(OrderItem.line_total).desc())
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).all()
        return [
            {
                "brand": row.brand,
                "order_count": int(row.order_count or 0),
                "quantity": int(row.quantity or 0),
                "revenue": int(row.revenue or 0),
            }
            for row in rows
        ]

    async def by_product(self, limit: int = 30) -> list[dict]:
        stmt = (
            select(
                OrderItem.product_id,
                OrderItem.product_slug,
                OrderItem.product_name,
                OrderItem.brand,
                func.sum(OrderItem.quantity).label("quantity"),
                func.sum(OrderItem.line_total).label("revenue"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.payment_status == PaymentStatus.verified.value)
            .group_by(
                OrderItem.product_id,
                OrderItem.product_slug,
                OrderItem.product_name,
                OrderItem.brand,
            )
            .order_by(func.sum(OrderItem.line_total).desc())
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).all()
        return [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "brand": row.brand,
                "slug": row.product_slug,
                "quantity": int(row.quantity or 0),
                "revenue": int(row.revenue or 0),
            }
            for row in rows
        ]
