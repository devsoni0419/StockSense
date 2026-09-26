from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.products import router as products_router
from app.api.v1.categories import router as categories_router
from app.api.v1.warehouses import router as warehouses_router
from app.api.v1.locations import router as locations_router
from app.api.v1.receipts import router as receipts_router
from app.api.v1.deliveries import router as deliveries_router
from app.api.v1.transfers import router as transfers_router
from app.api.v1.adjustments import router as adjustments_router
from app.api.v1.move_history import router as move_history_router
from app.api.v1.dashboard import router as dashboard_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(warehouses_router)
api_v1_router.include_router(locations_router)
api_v1_router.include_router(receipts_router)
api_v1_router.include_router(deliveries_router)
api_v1_router.include_router(transfers_router)
api_v1_router.include_router(adjustments_router)
api_v1_router.include_router(move_history_router)

__all__ = ["api_v1_router"]
