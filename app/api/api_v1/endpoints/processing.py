import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks
import structlog

from app.models.file_models import ProcessingRequest, ProcessingStatusResponse, ProcessingStatus
from app.services.session_manager import session_manager
from app.services.file_processor import file_processor
from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter()

async def process_file_background(session_id: str, tool_type: str, temp_path: str, filename: str, options: dict):
    try:
        # Update status to processing
        await session_manager.store_session_data(
            f"status:{session_id}",
            {
                "session_id": session_id,
                "status": ProcessingStatus.PROCESSING.value,
                "progress": 50,
                "message": "Processing file...",
                "started_at": datetime.now().isoformat()
            },
            expire_hours=1
        )
        
        # Process the file
        output_path, file_info = await file_processor.process_file(temp_path, tool_type, filename, options)
        
        # Store processed file info
        processed_data = {
            "output_path": output_path,
            "file_info": file_info,
            "expires_at": (datetime.now() + timedelta(hours=settings.PROCESSED_FILE_EXPIRE_HOURS)).isoformat()
        }
        
        await session_manager.store_session_data(
            f"processed:{session_id}",
            processed_data,
            expire_hours=settings.PROCESSED_FILE_EXPIRE_HOURS
        )
        
        # Update status to completed
        await session_manager.store_session_data(
            f"status:{session_id}",
            {
                "session_id": session_id,
                "status": ProcessingStatus.COMPLETED.value,
                "progress": 100,
                "message": "File processing completed",
                "completed_at": datetime.now().isoformat()
            },
            expire_hours=1
        )
        
        logger.info("File processing completed", session_id=session_id)
        
    except Exception as e:
        logger.error("File processing failed", error=str(e), session_id=session_id)
        
        await session_manager.store_session_data(
            f"status:{session_id}",
            {
                "session_id": session_id,
                "status": ProcessingStatus.FAILED.value,
                "progress": 0,
                "error": str(e)
            },
            expire_hours=1
        )

@router.post("/start", response_model=ProcessingStatusResponse)
async def start_processing(request: ProcessingRequest, background_tasks: BackgroundTasks):
    try:
        session_data = await session_manager.get_session_data(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Initialize processing status
        await session_manager.store_session_data(
            f"status:{request.session_id}",
            {
                "session_id": request.session_id,
                "status": ProcessingStatus.QUEUED.value,
                "progress": 0,
                "message": "Processing queued"
            },
            expire_hours=1
        )
        
        # Start background processing
        options = request.options or {}
        
        background_tasks.add_task(
            process_file_background,
            request.session_id,
            request.tool_type,
            session_data["temp_path"],
            session_data["original_filename"],
            options
        )
        
        logger.info("Processing started", session_id=request.session_id, tool_type=request.tool_type)
        
        return ProcessingStatusResponse(
            session_id=request.session_id,
            status=ProcessingStatus.QUEUED,
            progress=0,
            message="Processing started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start processing", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start processing")

@router.get("/status/{session_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(session_id: str):
    try:
        status_data = await session_manager.get_session_data(f"status:{session_id}")
        if not status_data:
            raise HTTPException(status_code=404, detail="Status not found")
        
        return ProcessingStatusResponse(**status_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get processing status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get status")
