from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    slug: str = Field(max_length=128)
    name: str = Field(max_length=255)
    brand: str = Field(max_length=64)
    category: str = Field(max_length=32)
    gender: str = Field(max_length=16)
    price: int = Field(gt=0)
    original_price: int | None = Field(None, alias="originalPrice")
    discount: int | None = Field(None, ge=0, le=100)
    drop: int = Field(ge=0)
    weight: int = Field(gt=0)
    stack_height: int | None = Field(None, alias="stackHeight")
    is_new: bool = Field(False, alias="isNew")
    is_bestseller: bool = Field(False, alias="isBestseller")
    is_special: bool = Field(False, alias="isSpecial")
    description: str
    images: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    foot_type: list[str] = Field(default_factory=list, alias="footType")
    surface: list[str] = Field(default_factory=list)
    sizes: list[int] = Field(default_factory=list)
    unavailable_sizes: list[int] = Field(default_factory=list, alias="unavailableSizes")

    model_config = {"populate_by_name": True}


class ProductUpdate(BaseModel):
    slug: str | None = None
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    gender: str | None = None
    price: int | None = Field(None, gt=0)
    original_price: int | None = Field(None, alias="originalPrice")
    discount: int | None = Field(None, ge=0, le=100)
    drop: int | None = Field(None, ge=0)
    weight: int | None = Field(None, gt=0)
    stack_height: int | None = Field(None, alias="stackHeight")
    is_new: bool | None = Field(None, alias="isNew")
    is_bestseller: bool | None = Field(None, alias="isBestseller")
    is_special: bool | None = Field(None, alias="isSpecial")
    description: str | None = None
    images: list[str] | None = None
    tags: list[str] | None = None
    foot_type: list[str] | None = Field(None, alias="footType")
    surface: list[str] | None = None
    sizes: list[int] | None = None
    unavailable_sizes: list[int] | None = Field(None, alias="unavailableSizes")

    model_config = {"populate_by_name": True}


class UploadResponse(BaseModel):
    url: str
