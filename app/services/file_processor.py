import os
import tempfile
import asyncio
from datetime import datetime
from typing import Tuple
from PIL import Image
import fitz  # PyMuPDF
import subprocess
import structlog

from app.core.exceptions import FileProcessingError
from app.models.file_models import ToolType

logger = structlog.get_logger()

def generate_output_filename(original_name: str, target_extension: str = None) -> str:
    parts = original_name.rsplit('.', 1)
    name_without_ext = parts[0]
    original_ext = parts[1] if len(parts) > 1 else ''
    
    date_str = datetime.now().strftime("%d%m%Y")
    final_extension = target_extension or original_ext
    
    return f"{name_without_ext}_created_by_dampdf_{date_str}.{final_extension}"

class FileProcessor:
    async def process_file(
        self, 
        input_path: str, 
        tool_type: ToolType, 
        original_filename: str,
        options: dict = None
    ) -> Tuple[str, dict]:
        try:
            logger.info("Processing file", tool_type=tool_type, filename=original_filename)
            
            # Generate output filename
            if tool_type in [ToolType.DOCX_TO_PDF, ToolType.XLSX_TO_PDF]:
                output_filename = generate_output_filename(original_filename, "pdf")
            else:
                output_filename = generate_output_filename(original_filename)
            
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, output_filename)
            
            # Process based on tool type
            if tool_type == ToolType.IMAGE_COMPRESS:
                await self._compress_image(input_path, output_path, options or {})
            elif tool_type == ToolType.PDF_COMPRESS:
                await self._compress_pdf(input_path, output_path, options or {})
            elif tool_type == ToolType.DOCX_TO_PDF:
                await self._convert_docx_to_pdf(input_path, output_path)
            elif tool_type == ToolType.XLSX_TO_PDF:
                await self._convert_xlsx_to_pdf(input_path, output_path)
            
            # Calculate file info
            original_size = os.path.getsize(input_path)
            processed_size = os.path.getsize(output_path)
            compression_ratio = ((original_size - processed_size) / original_size) * 100 if original_size > 0 else 0
            
            file_info = {
                "filename": output_filename,
                "original_size": original_size,
                "processed_size": processed_size,
                "compression_ratio": max(0, compression_ratio),
                "created_at": datetime.now()
            }
            
            return output_path, file_info
            
        except Exception as e:
            logger.error("File processing failed", error=str(e))
            raise FileProcessingError(f"Failed to process file: {str(e)}")
    
    async def _compress_image(self, input_path: str, output_path: str, options: dict):
        quality = options.get("quality", 70)
        
        with Image.open(input_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "JPEG", quality=quality, optimize=True)
    
    async def _compress_pdf(self, input_path: str, output_path: str, options: dict):
        compression_level = options.get("compression_level", "medium")
        
        doc = fitz.open(input_path)
        
        if compression_level == "high":
            deflate_level = 9
        elif compression_level == "medium":
            deflate_level = 6
        else:
            deflate_level = 3
        
        doc.save(output_path, deflate=True, deflate_level=deflate_level, garbage=4, clean=True)
        doc.close()
    
    async def _convert_docx_to_pdf(self, input_path: str, output_path: str):
        output_dir = os.path.dirname(output_path)
        
        cmd = ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, input_path]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
        
        if process.returncode != 0:
            raise FileProcessingError(f"LibreOffice conversion failed: {stderr.decode()}")
        
        generated_file = os.path.join(output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".pdf")
        
        if os.path.exists(generated_file):
            os.rename(generated_file, output_path)
        else:
            raise FileProcessingError("Converted file not found")
    
    async def _convert_xlsx_to_pdf(self, input_path: str, output_path: str):
        # Same as DOCX conversion
        await self._convert_docx_to_pdf(input_path, output_path)

# Global processor instance
file_processor = FileProcessor()
