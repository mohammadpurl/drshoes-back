"""Database bootstrap on application startup (tables + optional initial data)."""

import json
import logging
from pathlib import Path

from sqlalchemy import select, text

from app.config import settings
from app.core.security import hash_password
from app.database import AsyncSessionLocal, Base, engine, validate_database_url
from app.models import (  # noqa: F401 — register all models on Base.metadata
    Address,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    Review,
    ShopConfig,
    User,
)
from app.utils.ids import new_id

logger = logging.getLogger(__name__)

_DATA_PATH = settings.data_dir / "products.json"


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS "
                "videos JSONB NOT NULL DEFAULT '[]'::jsonb"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                "username VARCHAR(64)"
            )
        )
        await conn.execute(
            text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL")
        )
        for stmt in (
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS national_id VARCHAR(10)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS postal_code VARCHAR(16)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS address_line TEXT",
        ):
            await conn.execute(text(stmt))
        for stmt in (
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(32) DEFAULT 'awaiting_receipt'",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS receipt_url VARCHAR(512)",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS receipt_note TEXT",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS receipt_uploaded_at TIMESTAMPTZ",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_review_note TEXT",
            "UPDATE orders SET payment_status = 'awaiting_receipt' WHERE payment_status IS NULL",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_method VARCHAR(128)",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS tracking_number VARCHAR(64)",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_note TEXT",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipped_at TIMESTAMPTZ",
        ):
            await conn.execute(text(stmt))
    logger.info("Database tables ensured (create_all).")


async def ensure_shop_config(session) -> None:
    from app.models.shop_config import ShopConfig

    row = (
        await session.execute(select(ShopConfig).where(ShopConfig.id == 1))
    ).scalar_one_or_none()
    if not row:
        session.add(ShopConfig(id=1))
        logger.info("Default shop_config row created.")


def _username_from_email(email: str) -> str:
    local = email.split("@", 1)[0].lower()
    local = "".join(c for c in local if c.isalnum() or c in "._-") or "user"
    return local[:32]


async def migrate_users_to_username(session) -> None:
    """Backfill username for rows created before username-based auth."""
    result = await session.execute(select(User))
    users = result.scalars().all()
    used = {u.username for u in users if u.username}

    for user in users:
        if user.username:
            used.add(user.username)
            continue

        base = _username_from_email(user.email) if user.email else f"user_{user.id[:8]}"
        candidate = base[:32]
        suffix = 1
        while candidate in used or not candidate:
            tail = f"_{suffix}"
            candidate = f"{base[: 32 - len(tail)]}{tail}"
            suffix += 1

        user.username = candidate
        used.add(candidate)

        if not user.phone:
            user.phone = settings.admin_phone if user.is_admin else "09000000000"

    if users:
        logger.info("Ensured username for %s user(s).", len(users))


async def ensure_admin_user(session) -> bool:
    existing_admin = (
        await session.execute(
            select(User).where(User.username == settings.admin_username)
        )
    ).scalar_one_or_none()

    if not existing_admin and settings.admin_email:
        existing_admin = (
            await session.execute(
                select(User).where(User.email == settings.admin_email.lower())
            )
        ).scalar_one_or_none()

    if existing_admin:
        changed = False
        if not existing_admin.is_admin:
            existing_admin.is_admin = True
            changed = True
        if not existing_admin.username:
            existing_admin.username = settings.admin_username
            changed = True
        if not existing_admin.phone:
            existing_admin.phone = settings.admin_phone
            changed = True
        if changed:
            logger.info("Updated admin user: %s", settings.admin_username)
            return True
        return False

    session.add(
        User(
            id=new_id(),
            username=settings.admin_username,
            email=settings.admin_email.lower() if settings.admin_email else None,
            hashed_password=hash_password(settings.admin_password),
            full_name=settings.admin_full_name,
            phone=settings.admin_phone,
            is_admin=True,
        )
    )
    logger.info("Default admin created: %s", settings.admin_username)
    return True


def _product_from_dict(p: dict) -> Product:
    return Product(
        id=p["id"],
        slug=p["slug"],
        name=p["name"],
        brand=p["brand"],
        category=p["category"],
        gender=p["gender"],
        price=p["price"],
        original_price=p.get("originalPrice"),
        discount=p.get("discount"),
        drop_mm=p["drop"],
        weight=p["weight"],
        stack_height=p.get("stackHeight"),
        is_new=p.get("isNew", False),
        is_bestseller=p.get("isBestseller", False),
        is_special=p.get("isSpecial", False),
        description=p["description"],
        images=p.get("images", []),
        videos=p.get("videos", []),
        tags=p.get("tags", []),
        foot_types=p.get("footType", []),
        surfaces=p.get("surface", []),
        sizes=p.get("sizes", []),
        unavailable_sizes=p.get("unavailableSizes", []),
        rating=p.get("rating"),
        review_count=p.get("reviewCount", 0),
    )


def _review_from_dict(r: dict) -> Review:
    return Review(
        id=r["id"],
        product_id=r["productId"],
        author=r["author"],
        rating=r["rating"],
        date=r["date"],
        comment=r["comment"],
    )


async def seed_products_if_empty(session) -> int:
    """Load data/products.json when the catalog is empty (first run)."""
    existing = await session.execute(select(Product.id))
    if existing.first():
        return 0

    if not _DATA_PATH.exists():
        logger.warning("No products in DB and %s missing; catalog stays empty.", _DATA_PATH)
        return 0

    with _DATA_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    for p in data.get("products", []):
        session.add(_product_from_dict(p))
    for r in data.get("reviews", []):
        session.add(_review_from_dict(r))

    count = len(data.get("products", []))
    logger.info("Seeded %s products from products.json.", count)
    return count


async def bootstrap_database(*, seed_catalog: bool = True) -> None:
    """
    Run on app startup: create missing tables, default admin, optional catalog seed.
    Safe to call every time (idempotent).
    """
    validate_database_url()
    await create_tables()

    async with AsyncSessionLocal() as session:
        await migrate_users_to_username(session)
        await ensure_shop_config(session)
        await ensure_admin_user(session)
        if seed_catalog:
            await seed_products_if_empty(session)
        await session.commit()
