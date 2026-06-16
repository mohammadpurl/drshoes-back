from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    gender: Mapped[str] = mapped_column(String(16), index=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    original_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drop_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    stack_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_new: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bestseller: Mapped[bool] = mapped_column(Boolean, default=False)
    is_special: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    images: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    videos: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    foot_types: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    surfaces: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    sizes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    unavailable_sizes: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)

    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="product",
        cascade="all, delete-orphan",
    )
