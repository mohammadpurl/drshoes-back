import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate
from app.utils.ids import new_id


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _load_cart(self, cart_id: str) -> Cart | None:
        stmt = (
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_for_user(self, user: User) -> Cart:
        stmt = (
            select(Cart)
            .where(Cart.user_id == user.id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        result = await self.db.execute(stmt)
        cart = result.scalar_one_or_none()
        if cart:
            return cart

        cart = Cart(id=new_id(), user_id=user.id)
        self.db.add(cart)
        await self.db.commit()
        loaded = await self._load_cart(cart.id)
        if not loaded:
            raise RuntimeError("Failed to create cart")
        return loaded

    async def get_or_create_guest(self, session_token: str | None) -> tuple[Cart, str]:
        token = session_token or secrets.token_urlsafe(32)
        stmt = (
            select(Cart)
            .where(Cart.session_token == token)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        result = await self.db.execute(stmt)
        cart = result.scalar_one_or_none()
        if cart:
            return cart, token

        cart = Cart(id=new_id(), session_token=token)
        self.db.add(cart)
        await self.db.commit()
        loaded = await self._load_cart(cart.id)
        return loaded, token  # type: ignore[return-value]

    async def merge_guest_into_user(self, user: User, session_token: str) -> Cart:
        guest_stmt = (
            select(Cart)
            .where(Cart.session_token == session_token)
            .options(selectinload(Cart.items))
        )
        guest_result = await self.db.execute(guest_stmt)
        guest_cart = guest_result.scalar_one_or_none()

        user_cart = await self.get_or_create_for_user(user)
        if not guest_cart or guest_cart.id == user_cart.id:
            return user_cart

        for item in list(guest_cart.items):
            await self._upsert_item(user_cart, item.product_id, item.size, item.quantity)

        await self.db.delete(guest_cart)
        await self.db.commit()
        return await self._load_cart(user_cart.id)  # type: ignore[return-value]

    async def resolve_cart(
        self, user: User | None, session_token: str | None
    ) -> tuple[Cart, str | None]:
        if user:
            if session_token:
                cart = await self.merge_guest_into_user(user, session_token)
            else:
                cart = await self.get_or_create_for_user(user)
            return cart, None

        cart, token = await self.get_or_create_guest(session_token)
        return cart, token

    def _validate_size(self, product: Product, size: int) -> None:
        if size not in product.sizes:
            raise ValueError("سایز انتخاب‌شده برای این محصول موجود نیست")
        if size in product.unavailable_sizes:
            raise ValueError("این سایز ناموجود است")

    async def _upsert_item(
        self, cart: Cart, product_id: str, size: int, quantity: int
    ) -> CartItem:
        product_stmt = select(Product).where(Product.id == product_id)
        product = (await self.db.execute(product_stmt)).scalar_one_or_none()
        if not product:
            raise ValueError("محصول یافت نشد")
        self._validate_size(product, size)

        for item in cart.items:
            if item.product_id == product_id and item.size == size:
                item.quantity = quantity
                await self.db.commit()
                return item

        item = CartItem(
            id=new_id(),
            cart_id=cart.id,
            product_id=product_id,
            size=size,
            quantity=quantity,
        )
        self.db.add(item)
        await self.db.commit()
        return item

    async def add_item(
        self, cart: Cart, data: CartItemCreate
    ) -> Cart:
        await self._upsert_item(
            cart,
            data.product_id,
            data.size,
            data.quantity,
        )
        return await self._load_cart(cart.id)  # type: ignore[return-value]

    async def update_item_quantity(
        self, cart: Cart, item_id: str, quantity: int
    ) -> Cart | None:
        item = next((i for i in cart.items if i.id == item_id), None)
        if not item:
            return None
        item.quantity = quantity
        await self.db.commit()
        return await self._load_cart(cart.id)

    async def remove_item(self, cart: Cart, item_id: str) -> Cart | None:
        item = next((i for i in cart.items if i.id == item_id), None)
        if not item:
            return None
        await self.db.delete(item)
        await self.db.commit()
        return await self._load_cart(cart.id)

    async def clear(self, cart: Cart) -> Cart:
        for item in list(cart.items):
            await self.db.delete(item)
        await self.db.commit()
        return await self._load_cart(cart.id)  # type: ignore[return-value]

    @staticmethod
    def calc_subtotal(cart: Cart) -> tuple[int, int]:
        subtotal = 0
        count = 0
        for item in cart.items:
            if item.product:
                subtotal += item.product.price * item.quantity
                count += item.quantity
        return subtotal, count
