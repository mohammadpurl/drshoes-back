from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(max_length=64)
    full_name: str = Field(max_length=128, alias="fullName")
    phone: str = Field(max_length=20)
    province: str = Field(max_length=64)
    city: str = Field(max_length=64)
    address_line: str = Field(max_length=512, alias="addressLine")
    postal_code: str = Field(max_length=16, alias="postalCode")
    is_default: bool = Field(False, alias="isDefault")


class AddressUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    full_name: str | None = Field(None, alias="fullName")
    phone: str | None = None
    province: str | None = None
    city: str | None = None
    address_line: str | None = Field(None, alias="addressLine")
    postal_code: str | None = Field(None, alias="postalCode")
    is_default: bool | None = Field(None, alias="isDefault")


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

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_by_alias=True,
    )
