# File: app/api/api_v1/endpoints/download.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import structlog

from app.services.session_manager import session_manager

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/file/{session_id}")
async def download_file(session_id: str):
    try:
        session_data = await session_manager.get_session_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="File not found or expired")
        
        output_path = session_data.get("output_path")
        if not output_path or not os.path.exists(output_path):
            raise HTTPException(status_code=404, detail="Processed file not found")
        
        filename = session_data.get("file_info", {}).get("filename", "processed-file")
        
        # Track download
        await session_manager.track_usage(
            session_id=session_id,
            tool_type=session_data.get("tool_type"),
            file_size=os.path.getsize(output_path)
        )
        
        return FileResponse(
            path=output_path,
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error downloading file", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to download file")
