"""
Seed database from data/products.json (generated from frontend data/products.ts).

Usage (from Backend/):
  python -m scripts.seed
"""

import asyncio
import json
import sys
from pathlib import Path

# Allow running as python -m scripts.seed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import settings
from app.core.security import hash_password
from app.database import AsyncSessionLocal, Base, engine
from app.models import (  # noqa: F401 — register all tables on Base
    Address,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    Review,
    User,
)
from app.utils.ids import new_id


def load_seed_data() -> dict:
    path = Path(__file__).resolve().parent.parent / "data" / "products.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: npx tsx Backend/scripts/export_products.ts"
        )
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def product_from_dict(p: dict) -> Product:
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
        tags=p.get("tags", []),
        foot_types=p.get("footType", []),
        surfaces=p.get("surface", []),
        sizes=p.get("sizes", []),
        unavailable_sizes=p.get("unavailableSizes", []),
        rating=p.get("rating"),
        review_count=p.get("reviewCount", 0),
    )


def review_from_dict(r: dict) -> Review:
    return Review(
        id=r["id"],
        product_id=r["productId"],
        author=r["author"],
        rating=r["rating"],
        date=r["date"],
        comment=r["comment"],
    )


async def seed_admin(session) -> None:
    existing_user = await session.execute(select(User.id))
    if existing_user.first():
        return

    session.add(
        User(
            id=new_id(),
            email=settings.admin_email.lower(),
            hashed_password=hash_password(settings.admin_password),
            full_name=settings.admin_full_name,
            is_admin=True,
        )
    )
    print(f"Admin user: {settings.admin_email} / {settings.admin_password}")


async def seed() -> None:
    data = load_seed_data()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_admin(session)

        existing = await session.execute(select(Product.id))
        if existing.first():
            await session.commit()
            print("Products already seeded. Skipping product import.")
            return

        for p in data["products"]:
            session.add(product_from_dict(p))

        for r in data["reviews"]:
            session.add(review_from_dict(r))

        await session.commit()
        print(
            f"Seeded {len(data['products'])} products and {len(data['reviews'])} reviews."
        )


if __name__ == "__main__":
    asyncio.run(seed())
