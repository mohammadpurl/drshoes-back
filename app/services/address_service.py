from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressUpdate
from app.utils.ids import new_id


class AddressService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: str) -> list[Address]:
        stmt = select(Address).where(Address.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(self, user_id: str, address_id: str) -> Address | None:
        stmt = select(Address).where(
            Address.id == address_id, Address.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _clear_default(self, user_id: str) -> None:
        await self.db.execute(
            update(Address).where(Address.user_id == user_id).values(is_default=False)
        )

    async def create(self, user: User, data: AddressCreate) -> Address:
        if data.is_default:
            await self._clear_default(user.id)

        address = Address(
            id=new_id(),
            user_id=user.id,
            title=data.title,
            full_name=data.full_name,
            phone=data.phone,
            province=data.province,
            city=data.city,
            address_line=data.address_line,
            postal_code=data.postal_code,
            is_default=data.is_default,
        )
        self.db.add(address)
        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def update(
        self, user: User, address_id: str, data: AddressUpdate
    ) -> Address | None:
        address = await self.get_for_user(user.id, address_id)
        if not address:
            return None

        payload = data.model_dump(exclude_unset=True)
        if payload.get("is_default"):
            await self._clear_default(user.id)

        for key, value in payload.items():
            setattr(address, key, value)

        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def delete(self, user: User, address_id: str) -> bool:
        address = await self.get_for_user(user.id, address_id)
        if not address:
            return False
        await self.db.delete(address)
        await self.db.commit()
        return True
