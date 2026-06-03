from fastapi import APIRouter

from app.routes.admin.orders import router as admin_orders_router
from app.routes.admin.products import router as admin_products_router
from app.routes.admin.uploads import router as admin_uploads_router

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(admin_uploads_router, tags=["admin-uploads"])
admin_router.include_router(admin_products_router, prefix="/products", tags=["admin-products"])
admin_router.include_router(admin_orders_router, tags=["admin-orders"])
