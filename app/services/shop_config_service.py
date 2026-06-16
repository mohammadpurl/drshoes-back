from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shop_config import ShopConfig
from app.schemas.shop_config import PaymentInfoUpdate


class ShopConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self) -> ShopConfig:
        row = (await self.db.execute(select(ShopConfig).where(ShopConfig.id == 1))).scalar_one_or_none()
        if row:
            return row
        row = ShopConfig(id=1)
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def update_payment(self, data: PaymentInfoUpdate) -> ShopConfig:
        row = await self.get()
        row.payment_card_number = data.card_number
        row.payment_card_holder = data.card_holder
        row.payment_bank_name = data.bank_name
        row.payment_instructions = data.instructions
        await self.db.commit()
        await self.db.refresh(row)
        return row
