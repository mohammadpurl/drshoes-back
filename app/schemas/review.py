from pydantic import BaseModel, ConfigDict, Field


class ReviewRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_by_alias=True,
    )

    id: str
    productId: str = Field(validation_alias="product_id")
    author: str
    rating: int
    date: str
    comment: str

    def model_dump(self, **kwargs):
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=3, max_length=2000)
