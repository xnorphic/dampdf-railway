import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import structlog

from app.services.session_manager import session_manager

logger = structlog.get_logger()
router = APIRouter()

@router.get("/file/{session_id}")
async def download_file(session_id: str):
    try:
        processed_data = await session_manager.get_session_data(f"processed:{session_id}")
        if not processed_data:
            raise HTTPException(status_code=404, detail="File not found or expired")
        
        output_path = processed_data["output_path"]
        file_info = processed_data["file_info"]
        
        if not os.path.exists(output_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if file has expired
        expires_at = datetime.fromisoformat(processed_data["expires_at"])
        if datetime.now() > expires_at:
            try:
                os.remove(output_path)
            except:
                pass
            raise HTTPException(status_code=410, detail="File has expired")
        
        logger.info("File download started", session_id=session_id, filename=file_info["filename"])
        
        return FileResponse(
            path=output_path,
            filename=file_info["filename"],
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Download failed", error=str(e))
        raise HTTPException(status_code=500, detail="Download failed")
