from pydantic import BaseModel, Field

from app.schemas.product import ProductRead


class CartItemCreate(BaseModel):
    product_id: str = Field(alias="productId")
    size: int = Field(ge=35, le=50)
    quantity: int = Field(default=1, ge=1, le=10)

    model_config = {"populate_by_name": True}


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=10)


class CartItemRead(BaseModel):
    id: str
    productId: str = Field(validation_alias="product_id")
    size: int
    quantity: int
    product: ProductRead | None = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "ser_json_by_alias": True,
    }


class CartRead(BaseModel):
    id: str
    cartToken: str | None = Field(None, validation_alias="session_token")
    items: list[CartItemRead]
    itemCount: int = 0
    subtotal: int = 0
