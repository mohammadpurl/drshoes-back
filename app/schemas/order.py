from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.utils.media_urls import normalize_media_url


class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    preparing = "preparing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class PaymentStatus(str, Enum):
    awaiting_receipt = "awaiting_receipt"
    pending_review = "pending_review"
    verified = "verified"
    rejected = "rejected"


class CheckoutRequest(BaseModel):
    address_id: str = Field(alias="addressId")
    notes: str | None = Field(None, max_length=500)

    model_config = ConfigDict(populate_by_name=True)


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

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_by_alias=True,
    )

    @field_serializer("imageUrl")
    def serialize_image(self, value: str | None) -> str | None:
        return normalize_media_url(value) if value else None


class OrderRead(BaseModel):
    id: str
    status: str
    paymentStatus: str = Field(validation_alias="payment_status")
    receiptUrl: str | None = Field(None, validation_alias="receipt_url")
    receiptNote: str | None = Field(None, validation_alias="receipt_note")
    receiptUploadedAt: datetime | None = Field(
        None, validation_alias="receipt_uploaded_at"
    )
    paymentReviewNote: str | None = Field(
        None, validation_alias="payment_review_note"
    )
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
    shippingMethod: str | None = Field(None, validation_alias="shipping_method")
    trackingNumber: str | None = Field(None, validation_alias="tracking_number")
    shippingNote: str | None = Field(None, validation_alias="shipping_note")
    shippedAt: datetime | None = Field(None, validation_alias="shipped_at")
    createdAt: datetime = Field(validation_alias="created_at")
    items: list[OrderItemRead] = []

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_by_alias=True,
    )

    @field_serializer("receiptUrl")
    def serialize_receipt(self, value: str | None) -> str | None:
        return normalize_media_url(value) if value else None


class OrderListResponse(BaseModel):
    orders: list[OrderRead]
    total: int


class AdminOrderRead(OrderRead):
    userId: str = Field(validation_alias="user_id")
    username: str | None = None
    userFullName: str | None = None
    userPhone: str | None = None


class AdminOrderListResponse(BaseModel):
    orders: list[AdminOrderRead]
    total: int


class PaymentReviewRequest(BaseModel):
    action: str = Field(pattern="^(verify|reject)$")
    note: str | None = Field(None, max_length=500)

    model_config = ConfigDict(populate_by_name=True)


class OrderFulfillmentUpdate(BaseModel):
    status: OrderStatus | None = None
    shippingMethod: str | None = Field(None, max_length=128)
    trackingNumber: str | None = Field(None, max_length=64)
    shippingNote: str | None = Field(None, max_length=500)

    model_config = ConfigDict(populate_by_name=True)


class ReceiptUploadNote(BaseModel):
    note: str | None = Field(None, max_length=500)
