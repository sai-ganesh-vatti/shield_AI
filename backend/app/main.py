from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import router
from app.core.database import init_db, close_db, engine, Base
from app.seed_data import init_db_and_seed
import asyncio
import logging

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Digital Twin - India Pharmaceutical Logistics Network",
    description="Full-stack application for monitoring and managing India's pharmaceutical logistics network with real-time simulation",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def startup():
    """Initialize the application."""
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed default data
    await init_db_and_seed()
    logger.info("Database tables created and seeded")
    logger.info("Application started")


@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown."""
    await close_db()
    logger.info("Application shutdown complete")