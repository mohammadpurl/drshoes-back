from pydantic import BaseModel, Field


class AddressCreate(BaseModel):
    title: str = Field(max_length=64)
    full_name: str = Field(max_length=128)
    phone: str = Field(max_length=20)
    province: str = Field(max_length=64)
    city: str = Field(max_length=64)
    address_line: str = Field(max_length=512)
    postal_code: str = Field(max_length=16)
    is_default: bool = False


class AddressUpdate(BaseModel):
    title: str | None = None
    full_name: str | None = None
    phone: str | None = None
    province: str | None = None
    city: str | None = None
    address_line: str | None = None
    postal_code: str | None = None
    is_default: bool | None = None


class AddressRead(BaseModel):
    id: str
    title: str
    fullName: str = Field(validation_alias="full_name")
    phone: str
    province: str
    city: str
    addressLine: str = Field(validation_alias="address_line")
    postalCode: str = Field(validation_alias="postal_code")
    isDefault: bool = Field(validation_alias="is_default")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "ser_json_by_alias": True,
    }
