# File: app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import structlog
import uuid

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

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 DamPDF API starting on Railway")
    
    # Initialize session manager
    from app.services.session_manager import session_manager
    await session_manager.connect()
    
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
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    with structlog.contextvars.bound_contextvars(request_id=request_id):
        logger.debug("Request started", 
                    method=request.method, 
                    path=request.url.path,
                    client=request.client.host if request.client else None)
        
        response = await call_next(request)
        
        response.headers["X-Request-ID"] = request_id
        logger.debug("Request completed", status_code=response.status_code)
        
        return response

# Include API routes
from app.api.api_v1.api import api_router
app.include_router(api_router, prefix="/api/v1")

# Custom exception handler
from app.core.exceptions import DamPDFException
@app.exception_handler(DamPDFException)
async def dampdf_exception_handler(request: Request, exc: DamPDFException):
    logger.warning("DamPDF exception", 
                  error=str(exc), 
                  code=exc.code, 
                  path=request.url.path)
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "code": exc.code}
    )

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
