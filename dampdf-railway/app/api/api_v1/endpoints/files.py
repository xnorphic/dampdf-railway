import os
import tempfile
import aiofiles
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException
import structlog

from app.core.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.models.file_models import FileUploadResponse, ToolType
from app.services.session_manager import session_manager

logger = structlog.get_logger()
router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...), tool_type: ToolType = None):
    try:
        logger.info("File upload started", filename=file.filename, content_type=file.content_type)
        
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise FileTooLargeError(
                size_mb=file_size / (1024 * 1024),
                max_size_mb=settings.MAX_FILE_SIZE_MB
            )
        
        # Generate session ID
        session_id = session_manager.generate_session_id()
        
        # Save file to temporary location
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.filename)
        
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(content)
        
        # Store session data
        session_data = {
            "temp_path": temp_path,
            "original_filename": file.filename,
            "file_size": file_size,
            "content_type": file.content_type,
            "upload_time": datetime.now().isoformat(),
            "tool_type": tool_type.value if tool_type else None,
        }
        
        await session_manager.store_session_data(session_id, session_data, expire_hours=settings.TEMP_FILE_EXPIRE_HOURS)
        
        logger.info("File upload completed", session_id=session_id, filename=file.filename, size=file_size)
        
        return FileUploadResponse(
            session_id=session_id,
            filename=file.filename,
            size=file_size,
            file_type=file.content_type,
            upload_time=datetime.now()
        )
        
    except (FileTooLargeError, UnsupportedFileTypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("File upload failed", error=str(e))
        raise HTTPException(status_code=500, detail="File upload failed")
