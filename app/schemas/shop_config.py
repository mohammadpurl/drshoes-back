from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentInfoRead(BaseModel):
    cardNumber: str = Field(validation_alias="payment_card_number")
    cardHolder: str = Field(validation_alias="payment_card_holder")
    bankName: str = Field(validation_alias="payment_bank_name")
    instructions: str = Field(validation_alias="payment_instructions")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_by_alias=True,
    )


class PaymentInfoUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    card_number: str = Field(alias="cardNumber", max_length=32)
    card_holder: str = Field(alias="cardHolder", max_length=128)
    bank_name: str = Field(alias="bankName", max_length=64)
    instructions: str = Field(alias="instructions", max_length=2000)

    @field_validator("card_number")
    @classmethod
    def normalize_card(cls, value: str) -> str:
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) < 16:
            raise ValueError("شماره کارت باید حداقل ۱۶ رقم باشد")
        return digits
