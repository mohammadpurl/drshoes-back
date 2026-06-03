from fastapi import APIRouter

from app.routes.addresses import router as addresses_router
from app.routes.admin import admin_router
from app.routes.auth import router as auth_router
from app.routes.cart import router as cart_router
from app.routes.health import router as health_router
from app.routes.orders import router as orders_router
from app.routes.products import router as products_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(cart_router)
api_router.include_router(addresses_router)
api_router.include_router(orders_router)
api_router.include_router(admin_router)
