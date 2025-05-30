from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
import os
import structlog
import time

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

# Pydantic models for the new API endpoints
class ProcessRequest(BaseModel):
    fileId: str
    tool: str
    options: dict = {}

class UploadResponse(BaseModel):
    success: bool
    fileId: str
    message: str

class ProcessResponse(BaseModel):
    success: bool
    fileId: str
    tool: str
    downloadUrl: str
    originalSize: str
    newSize: str
    message: str

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

# FIXED CORS configuration for Railway + Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://dampdf-frontend.vercel.app",  # Your Vercel frontend
        "https://*.vercel.app",  # All Vercel preview deployments
    ],
    allow_credentials=False,  # Changed to False for better CORS compatibility
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing API routes
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
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "production")
    }

# NEW API ENDPOINTS for frontend compatibility

@app.post("/api/upload", response_model=UploadResponse)
async def upload_file():
    """Simple upload endpoint for frontend testing"""
    try:
        # Generate a test file ID
        file_id = f"test-file-{int(time.time())}"
        
        logger.info("File upload request received", file_id=file_id)
        
        return UploadResponse(
            success=True,
            fileId=file_id,
            message="File uploaded successfully"
        )
        
    except Exception as e:
        logger.error("Upload failed", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "success": False
        })

@app.post("/api/process", response_model=ProcessResponse)
async def process_file(request: ProcessRequest):
    """Simple processing endpoint for frontend testing"""
    try:
        logger.info("Processing request received", 
                   file_id=request.fileId, 
                   tool=request.tool)
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        return ProcessResponse(
            success=True,
            fileId=request.fileId,
            tool=request.tool,
            downloadUrl=f"/api/download/{request.fileId}",
            originalSize="1.2MB",
            newSize="456KB",
            message="File processed successfully"
        )
        
    except Exception as e:
        logger.error("Processing failed", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "success": False
        })

@app.get("/api/download/{file_id}")
async def download_file(file_id: str):
    """Simple download endpoint for frontend testing"""
    try:
        logger.info("Download request received", file_id=file_id)
        
        # For testing - return download info
        return {
            "message": f"Download ready for file: {file_id}",
            "fileId": file_id,
            "downloadUrl": f"https://dampdf-railway-production.up.railway.app/api/download/{file_id}",
            "success": True
        }
        
    except Exception as e:
        logger.error("Download failed", error=str(e))
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "success": False
        })

# Add OPTIONS handler for CORS preflight
@app.options("/api/{path:path}")
async def handle_options(path: str):
    """Handle CORS preflight requests"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Keep your existing error handler if you have one
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", 
                path=request.url.path, 
                method=request.method, 
                error=str(exc))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "path": request.url.path
        }
    )

if __name__ == "__main__":
    import uvicorn
    import asyncio
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
