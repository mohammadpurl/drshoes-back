from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ShopConfig(Base):
    """تنظیمات فروشگاه — یک ردیف (id=1)."""

    __tablename__ = "shop_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    payment_card_number: Mapped[str] = mapped_column(String(32), default="")
    payment_card_holder: Mapped[str] = mapped_column(String(128), default="")
    payment_bank_name: Mapped[str] = mapped_column(String(64), default="")
    payment_instructions: Mapped[str] = mapped_column(Text, default="")
