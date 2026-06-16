from pydantic import BaseModel, ConfigDict, Field


class ReportSummary(BaseModel):
    totalOrders: int = Field(validation_alias="total_orders")
    totalRevenue: int = Field(validation_alias="total_revenue")
    pendingPayments: int = Field(validation_alias="pending_payments")
    awaitingReceipt: int = Field(validation_alias="awaiting_receipt")
    confirmedOrders: int = Field(validation_alias="confirmed_orders")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class BrandReportRow(BaseModel):
    brand: str
    orderCount: int = Field(0, validation_alias="order_count")
    quantity: int = 0
    revenue: int = 0

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class ProductReportRow(BaseModel):
    productId: str = Field(validation_alias="product_id")
    productName: str = Field(validation_alias="product_name")
    brand: str
    slug: str = ""
    quantity: int = 0
    revenue: int = 0

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class BrandReportResponse(BaseModel):
    items: list[BrandReportRow]


class ProductReportResponse(BaseModel):
    items: list[ProductReportRow]
