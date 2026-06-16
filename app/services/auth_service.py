from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest, UserRead, UserUpdateRequest
from app.utils.ids import new_id
from app.utils.media_urls import normalize_media_url


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        stmt = select(User).where(User.phone == phone)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def register(self, data: RegisterRequest) -> User:
        username = data.username
        existing = await self.get_by_username(username)
        if existing:
            raise ValueError("این نام کاربری قبلاً ثبت شده است")

        phone_user = await self.get_by_phone(data.phone)
        if phone_user:
            raise ValueError("این شماره موبایل قبلاً ثبت شده است")

        user = User(
            id=new_id(),
            username=username,
            email=None,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            is_admin=False,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, username: str, password: str) -> User | None:
        user = await self.get_by_username(username)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def issue_token(self, user: User) -> str:
        return create_access_token(user.id)

    async def update_profile(self, user: User, data: UserUpdateRequest) -> User:
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return user

        if "email" in payload:
            email = payload["email"]
            if email:
                existing = await self.get_by_email(email)
                if existing and existing.id != user.id:
                    raise ValueError("این ایمیل قبلاً ثبت شده است")
            user.email = email

        for field in ("full_name", "national_id", "postal_code", "address_line"):
            if field in payload:
                setattr(user, field, payload[field])

        await self.db.commit()
        await self.db.refresh(user)
        return user

    def to_user_read(self, user: User) -> UserRead:
        read = UserRead.model_validate(user)
        if read.avatar_url:
            read = read.model_copy(
                update={"avatar_url": normalize_media_url(read.avatar_url)}
            )
        return read

    async def set_avatar(self, user: User, url: str) -> User:
        user.avatar_url = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def clear_avatar(self, user: User) -> User:
        user.avatar_url = None
        await self.db.commit()
        await self.db.refresh(user)
        return user
