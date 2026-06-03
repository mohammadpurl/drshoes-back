from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.product import (
    ProductFilters,
    ProductListResponse,
    ProductRead,
    SortOption,
)
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewRead
from app.services.product_service import ProductService
from app.services.review_service import ReviewService

router = APIRouter()


def parse_comma_list(value: str | None) -> list[str] | None:
    if not value or not value.strip():
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_int_list(value: str | None) -> list[int] | None:
    if not value or not value.strip():
        return None
    return [int(v.strip()) for v in value.split(",") if v.strip()]


@router.get("", response_model=ProductListResponse)
async def list_products(
    q: str | None = Query(None, description="جستجو"),
    category: str | None = Query(None),
    brands: str | None = Query(None, description="برندها با کاما"),
    sizes: str | None = Query(None, description="سایزها با کاما"),
    foot_type: str | None = Query(None, alias="footType"),
    surface: str | None = Query(None),
    gender: str | None = Query(None),
    min_price: int | None = Query(None, alias="minPrice"),
    max_price: int | None = Query(None, alias="maxPrice"),
    sort: SortOption = Query(SortOption.newest),
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
):
    filters = ProductFilters(
        q=q,
        category=category,
        brands=parse_comma_list(brands),
        sizes=parse_int_list(sizes),
        foot_type=parse_comma_list(foot_type),
        surface=parse_comma_list(surface),
        gender=gender,  # type: ignore[arg-type]
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        page=page,
        page_size=page_size,
    )

    service = ProductService(db)
    items, total = await service.list_products(filters)
    size = filters.page_size or settings.page_size
    loaded = (page - 1) * size + len(items)

    return ProductListResponse(
        products=[ProductRead.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=size,
        has_more=loaded < total,
    )


@router.get("/{slug}", response_model=ProductRead)
async def get_product(slug: str, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    product = await service.get_by_slug(slug)
    if not product:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")
    return ProductRead.model_validate(product)


@router.get("/{slug}/related", response_model=list[ProductRead])
async def get_related_products(
    slug: str,
    limit: int = Query(4, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    product = await service.get_by_slug(slug)
    if not product:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")
    related = await service.get_related(product, limit=limit)
    return [ProductRead.model_validate(p) for p in related]


@router.get("/{slug}/reviews", response_model=list[ReviewRead])
async def get_product_reviews(slug: str, db: AsyncSession = Depends(get_db)):
    product_service = ProductService(db)
    product = await product_service.get_by_slug(slug)
    if not product:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")

    review_service = ReviewService(db)
    reviews = await review_service.list_by_product_id(product.id)
    return [ReviewRead.model_validate(r) for r in reviews]


@router.post("/{slug}/reviews", response_model=ReviewRead, status_code=201)
async def create_product_review(
    slug: str,
    body: ReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product_service = ProductService(db)
    product = await product_service.get_by_slug(slug)
    if not product:
        raise HTTPException(status_code=404, detail="محصول یافت نشد")

    review_service = ReviewService(db)
    review = await review_service.create(product, user.full_name, body)
    return ReviewRead.model_validate(review)
