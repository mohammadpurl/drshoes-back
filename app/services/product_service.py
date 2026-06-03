from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.product import Product
from app.schemas.admin_product import ProductCreate, ProductUpdate
from app.schemas.product import ProductFilters, SortOption
from app.utils.ids import new_product_id


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _apply_filters(self, stmt: Select, filters: ProductFilters) -> Select:
        if filters.q and filters.q.strip():
            q = f"%{filters.q.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Product.name).like(q),
                    func.lower(Product.brand).like(q),
                    func.lower(Product.description).like(q),
                )
            )

        if filters.category and filters.category != "all":
            if filters.category == "women":
                stmt = stmt.where(Product.gender.in_(["women", "unisex"]))
            elif filters.category == "men":
                stmt = stmt.where(Product.gender.in_(["men", "unisex"]))
            else:
                stmt = stmt.where(Product.category == filters.category)

        if filters.brands:
            stmt = stmt.where(Product.brand.in_(filters.brands))

        if filters.gender:
            stmt = stmt.where(
                or_(Product.gender == filters.gender, Product.gender == "unisex")
            )

        if filters.min_price is not None:
            stmt = stmt.where(Product.price >= filters.min_price)

        if filters.max_price is not None:
            stmt = stmt.where(Product.price <= filters.max_price)

        if filters.sizes:
            stmt = stmt.where(
                or_(*[Product.sizes.contains([size]) for size in filters.sizes])
            )

        if filters.foot_type:
            stmt = stmt.where(
                or_(*[Product.foot_types.contains([ft]) for ft in filters.foot_type])
            )

        if filters.surface:
            stmt = stmt.where(
                or_(*[Product.surfaces.contains([surf]) for surf in filters.surface])
            )

        return stmt

    def _apply_sort(self, stmt: Select, sort: SortOption) -> Select:
        match sort:
            case SortOption.bestseller:
                return stmt.order_by(
                    Product.is_bestseller.desc(),
                    Product.is_new.desc(),
                    Product.price.asc(),
                )
            case SortOption.price_asc:
                return stmt.order_by(Product.price.asc())
            case SortOption.price_desc:
                return stmt.order_by(Product.price.desc())
            case _:
                return stmt.order_by(
                    Product.is_new.desc(),
                    Product.is_bestseller.desc(),
                    Product.price.desc(),
                )

    async def list_products(
        self, filters: ProductFilters
    ) -> tuple[list[Product], int]:
        page_size = filters.page_size or settings.page_size
        page = filters.page

        base = select(Product)
        base = self._apply_filters(base, filters)
        base = self._apply_sort(base, filters.sort)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = base.offset(offset).limit(page_size)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_slug(self, slug: str) -> Product | None:
        stmt = select(Product).where(Product.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_related(
        self, product: Product, limit: int = 4
    ) -> list[Product]:
        stmt = (
            select(Product)
            .where(Product.id != product.id)
            .where(
                or_(
                    Product.brand == product.brand,
                    Product.category == product.category,
                )
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, product_id: str) -> Product | None:
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: ProductCreate) -> Product:
        existing = await self.get_by_slug(data.slug)
        if existing:
            raise ValueError("اسلاگ تکراری است")

        product = Product(
            id=new_product_id(),
            slug=data.slug,
            name=data.name,
            brand=data.brand,
            category=data.category,
            gender=data.gender,
            price=data.price,
            original_price=data.original_price,
            discount=data.discount,
            drop_mm=data.drop,
            weight=data.weight,
            stack_height=data.stack_height,
            is_new=data.is_new,
            is_bestseller=data.is_bestseller,
            is_special=data.is_special,
            description=data.description,
            images=data.images,
            tags=data.tags,
            foot_types=data.foot_type,
            surfaces=data.surface,
            sizes=data.sizes,
            unavailable_sizes=data.unavailable_sizes,
        )
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update(self, product_id: str, data: ProductUpdate) -> Product | None:
        product = await self.get_by_id(product_id)
        if not product:
            return None

        payload = data.model_dump(exclude_unset=True, by_alias=False)
        field_map = {
            "drop": "drop_mm",
            "stack_height": "stack_height",
            "is_new": "is_new",
            "is_bestseller": "is_bestseller",
            "is_special": "is_special",
            "original_price": "original_price",
            "foot_type": "foot_types",
            "surface": "surfaces",
            "unavailable_sizes": "unavailable_sizes",
        }
        for key, value in payload.items():
            attr = field_map.get(key, key)
            if key == "slug" and value != product.slug:
                clash = await self.get_by_slug(value)
                if clash:
                    raise ValueError("اسلاگ تکراری است")
            setattr(product, attr, value)

        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete(self, product_id: str) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            return False
        await self.db.delete(product)
        await self.db.commit()
        return True
