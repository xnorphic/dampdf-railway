from pydantic import BaseModel, Field
from typing import Optional
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

class FileUploadResponse(BaseModel):
    session_id: str
    filename: str
    size: int
    file_type: str
    upload_time: datetime

class ProcessingRequest(BaseModel):
    session_id: str
    tool_type: ToolType
    options: Optional[dict] = None

class ProcessingStatusResponse(BaseModel):
    session_id: str
    status: ProcessingStatus
    progress: int = Field(ge=0, le=100)
    message: Optional[str] = None
    error: Optional[str] = None
