import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{3,32}$")
_PHONE_RE = re.compile(r"^09\d{9}$")
_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def _normalize_username(value: str) -> str:
    username = value.strip().lower()
    if not _USERNAME_RE.match(username):
        raise ValueError(
            "نام کاربری باید ۳ تا ۳۲ کاراکتر و فقط شامل حروف انگلیسی، عدد، نقطه، خط تیره و زیرخط باشد"
        )
    return username


def _normalize_phone(value: str) -> str:
    phone = value.strip().translate(_PERSIAN_DIGITS).replace(" ", "").replace("-", "")
    if phone.startswith("+98"):
        phone = "0" + phone[3:]
    elif phone.startswith("98") and len(phone) == 12:
        phone = "0" + phone[2:]
    if not _PHONE_RE.match(phone):
        raise ValueError("شماره موبایل معتبر نیست (مثال: 09121234567)")
    return phone


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=128, alias="fullName")
    phone: str = Field(min_length=11, max_length=20)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return _normalize_username(value)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _normalize_phone(value)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        name = value.strip()
        if len(name) < 2:
            raise ValueError("نام و نام خانوادگی الزامی است")
        return name


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return _normalize_username(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    full_name: str | None = Field(None, min_length=2, max_length=128, alias="fullName")
    email: str | None = None
    national_id: str | None = Field(None, max_length=10, alias="nationalId")
    postal_code: str | None = Field(None, max_length=16, alias="postalCode")
    address_line: str | None = Field(None, max_length=512, alias="addressLine")

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        name = value.strip()
        if len(name) < 2:
            raise ValueError("نام و نام خانوادگی الزامی است")
        return name

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        email = value.strip().lower()
        if "@" not in email or len(email) > 255:
            raise ValueError("ایمیل معتبر نیست")
        return email

    @field_validator("national_id")
    @classmethod
    def validate_national_id(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        digits = value.strip().translate(_PERSIAN_DIGITS)
        if not digits.isdigit() or len(digits) != 10:
            raise ValueError("کد ملی باید ۱۰ رقم باشد")
        return digits

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        code = value.strip().translate(_PERSIAN_DIGITS)
        if not code.isdigit() or len(code) != 10:
            raise ValueError("کد پستی باید ۱۰ رقم باشد")
        return code

    @field_validator("address_line")
    @classmethod
    def validate_address_line(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip()


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    full_name: str
    phone: str
    email: str | None = None
    is_admin: bool
    avatar_url: str | None = None
    national_id: str | None = None
    postal_code: str | None = None
    address_line: str | None = None


class ProfileAvatarResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    avatar_url: str = Field(serialization_alias="avatarUrl")
    url: str
