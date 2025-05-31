# File: app/models/file_models.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class ProcessingStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ToolType(str, Enum):
    IMAGE_COMPRESS = "image-compress"
    PDF_COMPRESS = "pdf-compress"
    DOCX_TO_PDF = "docx-to-pdf"
    XLSX_TO_PDF = "xlsx-to-pdf"

class UserPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class FileUploadResponse(BaseModel):
    session_id: str
    filename: str
    size: int
    file_type: str
    upload_time: datetime

class ProcessingRequest(BaseModel):
    session_id: str
    tool_type: ToolType
    options: Optional[Dict[str, Any]] = None

class ProcessingStatusResponse(BaseModel):
    session_id: str
    status: ProcessingStatus
    progress: int = Field(ge=0, le=100)
    message: Optional[str] = None
    error: Optional[str] = None

class PlanFeatures(BaseModel):
    max_file_size_mb: int
    daily_conversions: int
    priority_processing: bool
    advanced_compression: bool
    batch_processing: bool
    watermark_removal: bool
    api_access: bool

# Plan features configuration
PLAN_FEATURES = {
    UserPlan.FREE: PlanFeatures(
        max_file_size_mb=10,
        daily_conversions=5,
        priority_processing=False,
        advanced_compression=False,
        batch_processing=False,
        watermark_removal=False,
        api_access=False
    ),
    UserPlan.BASIC: PlanFeatures(
        max_file_size_mb=50,
        daily_conversions=50,
        priority_processing=False,
        advanced_compression=True,
        batch_processing=False,
        watermark_removal=True,
        api_access=False
    ),
    UserPlan.PREMIUM: PlanFeatures(
        max_file_size_mb=100,
        daily_conversions=500,
        priority_processing=True,
        advanced_compression=True,
        batch_processing=True,
        watermark_removal=True,
        api_access=True
    ),
    UserPlan.ENTERPRISE: PlanFeatures(
        max_file_size_mb=500,
        daily_conversions=5000,
        priority_processing=True,
        advanced_compression=True,
        batch_processing=True,
        watermark_removal=True,
        api_access=True
    )
}
