from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_cart_token, get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead, UserUpdateRequest
from app.services.auth_service import AuthService
from app.services.cart_service import CartService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    cart_token: str | None = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        user = await service.register(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if cart_token:
        await CartService(db).merge_guest_into_user(user, cart_token)

    return TokenResponse(access_token=service.issue_token(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    cart_token: str | None = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=401, detail="نام کاربری یا رمز عبور اشتباه است"
        )

    if cart_token:
        await CartService(db).merge_guest_into_user(user, cart_token)

    return TokenResponse(access_token=service.issue_token(user))


@router.get("/me", response_model=UserRead)
async def me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return service.to_user_read(user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    body: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        updated = await service.update_profile(user, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return service.to_user_read(updated)
