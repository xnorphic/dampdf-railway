from fastapi import APIRouter
from app.api.api_v1.endpoints import files, processing, download

api_router = APIRouter()

api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(processing.router, prefix="/process", tags=["processing"])
api_router.include_router(download.router, prefix="/download", tags=["download"])
