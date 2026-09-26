from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, engine
from app.api.v1 import api_v1_router
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("StockSense")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    logger.info("Starting up StockSense IMS API...")
    try:
        init_db()
    except Exception as e:
        logger.error(f"Startup database check: {e}")
    yield
    logger.info("Shutting down StockSense IMS API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
# StockSense - Modern Modular Inventory Management System (IMS) API
Digitize and streamline enterprise stock-related operations with real-time tracking, multi-warehouse support, automated ledger, and role-based access.

### Core Modules:
- **Authentication**: JWT authentication, OTP-based password reset, and user profile management.
- **Dashboard & KPIs**: Real-time stock counts, low stock alerts, pending operations, and multi-faceted dynamic filters.
- **Products & Stock Availability**: Multi-warehouse stock breakdown, custom units of measure, and automated reorder rules.
- **Operations - Receipts**: Incoming goods tracking, vendor deliveries, and automatic inventory increments upon validation.
- **Operations - Delivery Orders**: Outgoing customer shipments with picking, packing, and validation workflow.
- **Operations - Internal Transfers**: Cross-location & cross-warehouse transfers with conservation of total inventory.
- **Operations - Stock Adjustments**: Fast physical count reconciliation and automatic damaged/loss adjustment.
- **Move History & Stock Ledger**: Comprehensive immutable audit ledger of every single stock movement.
- **Settings**: Multi-warehouse and location/zone management.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db


@app.get("/", tags=["Health & System"])
def root_health_check(db: Session = Depends(get_db)):
    """Health check and API overview."""
    db_status = "unknown"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected ({str(e)})"

    return {
        "status": "online",
        "app_name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database_status": db_status,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_v1": settings.API_V1_PREFIX
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
