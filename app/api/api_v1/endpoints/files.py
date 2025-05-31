# File: app/api/api_v1/endpoints/files.py

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import os
import tempfile
import shutil
from datetime import datetime
import structlog

from app.core.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.models.file_models import FileUploadResponse, ProcessingStatus
from app.services.session_manager import session_manager

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    tool_type: str = Form(...)
):
    try:
        # Validate file size
        file_size = 0
        temp_file_path = None
        
        try:
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Save uploaded file to temp file
            with open(temp_file_path, "wb") as buffer:
                # Read in chunks to avoid memory issues with large files
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    file_size += len(chunk)
                    buffer.write(chunk)
                    
                    # Check size limit during upload
                    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                        os.unlink(temp_file_path)
                        raise FileTooLargeError(file_size / (1024 * 1024), settings.MAX_FILE_SIZE_MB)
            
            # Validate file type based on tool
            await validate_file_type(temp_file_path, file.content_type, tool_type)
            
            # Generate session
            session_id = session_manager.generate_session_id()
            
            # Store session data
            session_data = {
                "session_id": session_id,
                "filename": file.filename,
                "original_filename": file.filename,
                "file_path": temp_file_path,
                "file_type": file.content_type,
                "size": file_size,
                "tool_type": tool_type,
                "status": ProcessingStatus.QUEUED,
                "upload_time": datetime.now(),
                "progress": 0
            }
            
            await session_manager.store_session_data(
                session_id, 
                session_data,
                expire_hours=settings.TEMP_FILE_EXPIRE_HOURS
            )
            
            # Track usage
            await session_manager.track_usage(
                session_id=session_id,
                tool_type=tool_type,
                file_size=file_size
            )
            
            return FileUploadResponse(
                session_id=session_id,
                filename=file.filename,
                size=file_size,
                file_type=file.content_type,
                upload_time=session_data["upload_time"]
            )
            
        except Exception as e:
            # Clean up temp file if there was an error
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise
            
    except FileTooLargeError as e:
        logger.warning("File too large", error=str(e))
        return JSONResponse(
            status_code=413,  # Payload Too Large
            content={"error": str(e), "code": e.code}
        )
    except UnsupportedFileTypeError as e:
        logger.warning("Unsupported file type", error=str(e))
        return JSONResponse(
            status_code=415,  # Unsupported Media Type
            content={"error": str(e), "code": e.code}
        )
    except Exception as e:
        logger.exception("File upload failed", error=str(e))
        return JSONResponse(
            status_code=500,
            content={"error": "File upload failed", "code": "UPLOAD_ERROR"}
        )

async def validate_file_type(file_path: str, content_type: str, tool_type: str):
    """Validate that the file type is appropriate for the selected tool"""
    valid_types = {
        "image-compress": ["image/jpeg", "image/png", "image/webp", "image/gif"],
        "pdf-compress": ["application/pdf"],
        "docx-to-pdf": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"],
        "xlsx-to-pdf": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]
    }
    
    if tool_type in valid_types and content_type not in valid_types[tool_type]:
        raise UnsupportedFileTypeError(content_type)
