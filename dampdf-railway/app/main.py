from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 DamPDF API starting on Railway")
    yield
    logger.info("🛑 DamPDF API shutting down")

app = FastAPI(
    title="DamPDF API",
    version="1.0.0",
    description="Smarter. Smaller. Simpler.",
    lifespan=lifespan
)

# CORS configuration for Railway
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dampdf-frontend.vercel.app",
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)allow_headers=["*"],
)

# Include API routes
from app.api.api_v1.api import api_router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "DamPDF API is running on Railway! 🚂",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "DamPDF API",
        "platform": "Railway",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development")
    }
