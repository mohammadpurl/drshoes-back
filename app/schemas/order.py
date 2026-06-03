from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class CheckoutRequest(BaseModel):
    address_id: str = Field(alias="addressId")
    notes: str | None = Field(None, max_length=500)

    model_config = {"populate_by_name": True}


class OrderItemRead(BaseModel):
    id: str
    productId: str = Field(validation_alias="product_id")
    productSlug: str = Field(validation_alias="product_slug")
    productName: str = Field(validation_alias="product_name")
    brand: str
    imageUrl: str | None = Field(None, validation_alias="image_url")
    size: int
    quantity: int
    unitPrice: int = Field(validation_alias="unit_price")
    lineTotal: int = Field(validation_alias="line_total")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "ser_json_by_alias": True,
    }


class OrderRead(BaseModel):
    id: str
    status: str
    subtotal: int
    shippingCost: int = Field(validation_alias="shipping_cost")
    total: int
    notes: str | None = None
    shippingFullName: str = Field(validation_alias="shipping_full_name")
    shippingPhone: str = Field(validation_alias="shipping_phone")
    shippingProvince: str = Field(validation_alias="shipping_province")
    shippingCity: str = Field(validation_alias="shipping_city")
    shippingAddress: str = Field(validation_alias="shipping_address")
    shippingPostalCode: str = Field(validation_alias="shipping_postal_code")
    createdAt: datetime = Field(validation_alias="created_at")
    items: list[OrderItemRead] = []

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "ser_json_by_alias": True,
    }


class OrderListResponse(BaseModel):
    orders: list[OrderRead]
    total: int
