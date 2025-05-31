# File: app/api/api_v1/api.py

from fastapi import APIRouter
from app.api.api_v1.endpoints import files, process, download, pricing

api_router = APIRouter()
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(process.router, prefix="/process", tags=["Processing"])
api_router.include_router(download.router, prefix="/download", tags=["Download"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["Pricing"])
