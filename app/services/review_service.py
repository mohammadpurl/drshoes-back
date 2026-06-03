from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.review import Review
from app.schemas.review import ReviewCreate
from app.utils.ids import new_id


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_product_id(self, product_id: str) -> list[Review]:
        stmt = (
            select(Review)
            .where(Review.product_id == product_id)
            .order_by(Review.id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self, product: Product, author: str, data: ReviewCreate
    ) -> Review:
        review = Review(
            id=new_id(),
            product_id=product.id,
            author=author,
            rating=data.rating,
            date=datetime.now(UTC).strftime("%Y/%m/%d"),
            comment=data.comment,
        )
        self.db.add(review)

        prev_count = product.review_count or 0
        prev_rating = product.rating or 0.0
        new_count = prev_count + 1
        new_avg = (
            (prev_rating * prev_count + data.rating) / new_count
            if prev_count
            else float(data.rating)
        )

        await self.db.execute(
            update(Product)
            .where(Product.id == product.id)
            .values(rating=round(new_avg, 1), review_count=new_count)
        )

        await self.db.commit()
        await self.db.refresh(review)
        return review
