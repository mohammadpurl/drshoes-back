from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SortOption(str, Enum):
    newest = "newest"
    bestseller = "bestseller"
    price_asc = "price_asc"
    price_desc = "price_desc"


class ProductRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_by_alias=True,
    )

    id: str
    slug: str
    name: str
    brand: str
    category: str
    gender: str
    price: int
    originalPrice: int | None = Field(None, validation_alias="original_price")
    discount: int | None = None
    sizes: list[int]
    unavailableSizes: list[int] = Field(
        default_factory=list, validation_alias="unavailable_sizes"
    )
    footType: list[str] = Field(validation_alias="foot_types")
    surface: list[str] = Field(validation_alias="surfaces")
    drop: int = Field(validation_alias="drop_mm")
    weight: int
    stackHeight: int | None = Field(None, validation_alias="stack_height")
    isNew: bool = Field(validation_alias="is_new")
    isBestseller: bool = Field(validation_alias="is_bestseller")
    isSpecial: bool = Field(False, validation_alias="is_special")
    images: list[str]
    description: str
    tags: list[str]
    rating: float | None = None
    reviewCount: int = Field(0, validation_alias="review_count")

    def model_dump(self, **kwargs):
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


class ProductListResponse(BaseModel):
    products: list[ProductRead]
    total: int
    page: int
    page_size: int
    has_more: bool


class ProductFilters(BaseModel):
    q: str | None = None
    category: str | None = None
    brands: list[str] | None = None
    sizes: list[int] | None = None
    foot_type: list[str] | None = None
    surface: list[str] | None = None
    gender: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    sort: SortOption = SortOption.newest
    page: int = Field(1, ge=1)
    page_size: int | None = None
