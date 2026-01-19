"""Search API endpoints"""
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from typing import Optional
import logging

from ..models.schemas import SearchResponse, PhotoListResponse, PhotoItem
from ..services.search_service import search_service
from ..services.face_detector import face_detector
from ..services.image_store import image_store
from ..core.config import settings
from ..core.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_by_face(
    file: UploadFile = File(..., description="Query image file"),
    top_k: int = Query(
        default=settings.default_top_k,
        ge=1,
        le=100,
        description="Maximum number of results"
    ),
    threshold: float = Query(
        default=settings.default_similarity_threshold,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold"
    ),
    event_tag: Optional[str] = Query(
        default=None,
        description="Optional event tag filter"
    )
):
    """
    Search for similar faces by uploading a query image
    
    - Upload an image containing a face
    - Returns similar faces from the database
    - Results are ranked by similarity score
    - Optionally filter by event tag
    """
    try:
        # Initialize face detector if not already done
        face_detector.initialize()
        
        # Read uploaded file
        image_data = await file.read()
        
        logger.info(
            f"Search request: filename={file.filename}, "
            f"top_k={top_k}, threshold={threshold}, event_tag={event_tag}"
        )
        
        # Perform search
        results, query_time, face_detected = search_service.search_by_image(
            image_data=image_data,
            top_k=top_k,
            threshold=threshold,
            event_tag=event_tag
        )
        
        if not face_detected:
            logger.warning("No face detected in uploaded image")
            return SearchResponse(
                results=[],
                query_time_ms=round(query_time, 2),
                face_detected=False,
                message="No face detected in the uploaded image. Please upload an image containing a clear face."
            )
        
        logger.info(f"Search completed in {query_time:.2f}ms, found {len(results)} results")
        
        message = None
        if len(results) == 0:
            message = "No matching faces found in the database. Try adjusting the similarity threshold."
        
        return SearchResponse(
            results=results,
            query_time_ms=round(query_time, 2),
            face_detected=True,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/photos", response_model=PhotoListResponse)
async def list_photos(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    event_tag: Optional[str] = Query(default=None, description="Filter by event tag")
):
    """
    List all photos in the database with pagination
    
    - Returns photos with primary faces
    - Supports pagination (default 20 per page)
    - Optionally filter by event tag
    """
    try:
        db = get_db()
        offset = (page - 1) * page_size
        
        # Build query
        count_query = "SELECT COUNT(*) as count FROM photos"
        list_query = """
            SELECT p.id, p.path, p.width, p.height, p.event_tag, p.created_at
            FROM photos p
            WHERE EXISTS (
                SELECT 1 FROM faces f 
                WHERE f.photo_id = p.id AND f.is_primary = true
            )
        """
        
        params = []
        if event_tag:
            count_query += " WHERE event_tag = %s"
            list_query += " AND p.event_tag = %s"
            params.append(event_tag)
        
        # Get total count
        if params:
            total_result = db.execute_one(count_query, tuple(params))
        else:
            total_result = db.execute_one(count_query)
        total = total_result['count'] if total_result else 0
        
        # Get photos
        list_query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])
        
        results = db.execute(list_query, tuple(params))
        
        photos = []
        if results:
            for row in results:
                image_url = image_store.get_image_url(row['path'])
                photos.append(
                    PhotoItem(
                        photo_id=str(row['id']),
                        image_url=image_url,
                        event_tag=row['event_tag'],
                        width=row['width'],
                        height=row['height'],
                        created_at=row['created_at']
                    )
                )
        
        total_pages = (total + page_size - 1) // page_size
        
        logger.info(f"Listed {len(photos)} photos (page {page}/{total_pages})")
        
        return PhotoListResponse(
            photos=photos,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Failed to list photos: {e}")
        raise HTTPException(status_code=500, detail=str(e))
