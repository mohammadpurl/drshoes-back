from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_admin_user
from app.database import get_db
from app.models.user import User
from app.schemas.report import (
    BrandReportResponse,
    BrandReportRow,
    ProductReportResponse,
    ProductReportRow,
    ReportSummary,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports")


@router.get("")
async def report_bundle(
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    summary = await service.summary()
    by_brand = await service.by_brand()
    by_product = await service.by_product()
    return {
        "summary": {
            "totalOrders": summary["total_orders"],
            "totalRevenue": summary["total_revenue"],
            "pendingPaymentCount": summary["pending_payments"],
            "awaitingReceiptCount": summary["awaiting_receipt"],
            "verifiedPaymentCount": summary["verified_payments"],
        },
        "byBrand": [
            {
                "brand": row["brand"],
                "orderCount": row["order_count"],
                "unitsSold": row["quantity"],
                "revenue": row["revenue"],
            }
            for row in by_brand
        ],
        "byProduct": [
            {
                "productId": row["product_id"],
                "productName": row["product_name"],
                "brand": row["brand"],
                "slug": row.get("slug", ""),
                "unitsSold": row["quantity"],
                "revenue": row["revenue"],
            }
            for row in by_product
        ],
    }


@router.get("/summary", response_model=ReportSummary)
async def report_summary(
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    data = await ReportService(db).summary()
    return ReportSummary.model_validate(
        {
            "total_orders": data["total_orders"],
            "total_revenue": data["total_revenue"],
            "pending_payments": data["pending_payments"],
            "awaiting_receipt": data["awaiting_receipt"],
            "confirmed_orders": data["confirmed_orders"],
        }
    )


@router.get("/by-brand", response_model=BrandReportResponse)
@router.get("/brands", response_model=BrandReportResponse)
async def report_by_brand(
    limit: int = Query(20, ge=1, le=100),
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    items = await ReportService(db).by_brand(limit=limit)
    return BrandReportResponse(
        items=[BrandReportRow.model_validate(i) for i in items]
    )


@router.get("/by-product", response_model=ProductReportResponse)
@router.get("/products", response_model=ProductReportResponse)
async def report_by_product(
    limit: int = Query(30, ge=1, le=100),
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    items = await ReportService(db).by_product(limit=limit)
    return ProductReportResponse(
        items=[ProductReportRow.model_validate(i) for i in items]
    )
