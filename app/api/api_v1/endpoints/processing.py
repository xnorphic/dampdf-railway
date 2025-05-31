# File: app/api/api_v1/endpoints/process.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import os
import structlog

from app.core.exceptions import DamPDFException, FileProcessingError
from app.models.file_models import ProcessingRequest, ProcessingStatusResponse, ProcessingStatus
from app.services.file_processor import file_processor
from app.services.session_manager import session_manager
from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/start", response_model=ProcessingStatusResponse)
async def start_processing(request: ProcessingRequest, background_tasks: BackgroundTasks):
    try:
        # Get session data
        session_data = await session_manager.get_session_data(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Update status to processing
        session_data["status"] = ProcessingStatus.PROCESSING
        session_data["progress"] = 10
        session_data["message"] = "Processing started"
        await session_manager.store_session_data(
            request.session_id, 
            session_data,
            expire_hours=settings.TEMP_FILE_EXPIRE_HOURS
        )
        
        # Get file path from session
        input_path = session_data.get("file_path")
        if not input_path or not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Start processing in background
        background_tasks.add_task(
            process_file_background,
            request.session_id,
            input_path,
            request.tool_type,
            session_data.get("filename", "file"),
            request.options or {}
        )
        
        return ProcessingStatusResponse(
            session_id=request.session_id,
            status=ProcessingStatus.PROCESSING,
            progress=10,
            message="Processing started"
        )
        
    except HTTPException:
        raise
    except DamPDFException as e:
        logger.warning("Processing request failed", error=str(e), code=e.code)
        return JSONResponse(
            status_code=400,
            content={"error": str(e), "code": e.code}
        )
    except Exception as e:
        logger.exception("Unexpected error in processing request", error=str(e))
        return JSONResponse(
            status_code=500,
            content={"error": "An unexpected error occurred", "code": "INTERNAL_ERROR"}
        )

async def process_file_background(
    session_id: str,
    input_path: str,
    tool_type: str,
    original_filename: str,
    options: dict
):
    try:
        # Update status
        session_data = await session_manager.get_session_data(session_id)
        if not session_data:
            logger.error("Session not found during background processing", session_id=session_id)
            return
        
        session_data["progress"] = 30
        session_data["message"] = "Processing file..."
        await session_manager.store_session_data(
            session_id, 
            session_data,
            expire_hours=settings.TEMP_FILE_EXPIRE_HOURS
        )
        
        # Process the file
        output_path, file_info = await file_processor.process_file(
            input_path, tool_type, original_filename, options
        )
        
        # Update session with result
        session_data["status"] = ProcessingStatus.COMPLETED
        session_data["progress"] = 100
        session_data["message"] = "Processing complete"
        session_data["output_path"] = output_path
        session_data["file_info"] = file_info
        
        # Store session with longer expiry for processed files
        await session_manager.store_session_data(
            session_id, 
            session_data,
            expire_hours=settings.PROCESSED_FILE_EXPIRE_HOURS
        )
        
        logger.info("File processing completed", session_id=session_id)
        
    except Exception as e:
        logger.exception("Background processing failed", session_id=session_id, error=str(e))
        
        # Update session with error
        try:
            session_data = await session_manager.get_session_data(session_id)
            if session_data:
                session_data["status"] = ProcessingStatus.FAILED
                session_data["error"] = str(e)
                await session_manager.store_session_data(
                    session_id, 
                    session_data,
                    expire_hours=settings.TEMP_FILE_EXPIRE_HOURS
                )
        except Exception as update_error:
            logger.error("Failed to update session with error", error=str(update_error))

@router.get("/status/{session_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(session_id: str):
    try:
        session_data = await session_manager.get_session_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        return ProcessingStatusResponse(
            session_id=session_id,
            status=session_data.get("status", ProcessingStatus.QUEUED),
            progress=session_data.get("progress", 0),
            message=session_data.get("message", ""),
            error=session_data.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting processing status", session_id=session_id, error=str(e))
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get processing status", "code": "INTERNAL_ERROR"}
        )
