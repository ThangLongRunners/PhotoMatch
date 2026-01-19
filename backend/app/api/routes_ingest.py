"""Ingest API endpoints"""
from fastapi import APIRouter, HTTPException, UploadFile, File
import logging
import shutil
from pathlib import Path
from datetime import datetime

from ..models.schemas import IngestFolderRequest, IngestFolderResponse
from ..services.ingest_service import ingest_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload a single image file
    
    - Saves uploaded image temporarily
    - Detects faces and selects largest
    - Generates embeddings
    - Stores in database
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create uploads directory if not exists
        upload_dir = Path("/app/data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(file.filename).suffix if file.filename else ".jpg"
        temp_path = upload_dir / f"{timestamp}_{file.filename}"
        
        # Save uploaded file
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded: {temp_path}")
        
        # Process single image
        stats = ingest_service.ingest_folder(
            folder_path=str(upload_dir),
            recursive=False,
            event_tag=None
        )
        
        return {
            "success": True,
            "message": f"Image uploaded and processed successfully",
            "filename": file.filename,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/folder", response_model=IngestFolderResponse)
async def ingest_folder(request: IngestFolderRequest):
    """
    Ingest all images from a folder
    
    - Walks through folder (recursively if specified)
    - Hashes each image (SHA1)
    - Skips duplicates
    - Detects faces and selects largest
    - Generates embeddings
    - Stores in database
    """
    try:
        logger.info(
            f"Starting folder ingest: path={request.path}, "
            f"recursive={request.recursive}, event_tag={request.event_tag}"
        )
        
        stats = ingest_service.ingest_folder(
            folder_path=request.path,
            recursive=request.recursive,
            event_tag=request.event_tag
        )
        
        message = (
            f"Ingestion complete: {stats['processed']} images processed, "
            f"{stats['skipped']} skipped, {stats['errors']} errors"
        )
        
        return IngestFolderResponse(
            processed=stats['processed'],
            skipped=stats['skipped'],
            errors=stats['errors'],
            message=message
        )
        
    except Exception as e:
        logger.error(f"Folder ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
