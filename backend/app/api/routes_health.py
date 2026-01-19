"""Health check endpoint"""
from fastapi import APIRouter
from datetime import datetime
import logging

from ..models.schemas import HealthResponse, StatsResponse
from ..core.config import settings
from ..core.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify service status"""
    
    # Check database connection
    db_status = "disconnected"
    try:
        db = get_db()
        result = db.execute_one("SELECT 1 as test")
        if result:
            db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(),
        database=db_status,
        face_model=settings.embedding_model
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get database statistics including photo and face counts"""
    
    try:
        db = get_db()
        
        # Count total photos
        photo_result = db.execute_one("SELECT COUNT(*) as count FROM photos")
        total_photos = photo_result['count'] if photo_result else 0
        
        # Count total faces
        face_result = db.execute_one("SELECT COUNT(*) as count FROM faces")
        total_faces = face_result['count'] if face_result else 0
        
        # Count primary faces
        primary_result = db.execute_one(
            "SELECT COUNT(*) as count FROM faces WHERE is_primary = true"
        )
        primary_faces = primary_result['count'] if primary_result else 0
        
        # Get distinct event tags
        event_tags = []
        tag_results = db.execute(
            "SELECT DISTINCT event_tag FROM photos WHERE event_tag IS NOT NULL ORDER BY event_tag"
        )
        if tag_results:
            event_tags = [row['event_tag'] for row in tag_results]
        
        # Get database size (optional, may fail based on permissions)
        db_size_mb = None
        try:
            size_result = db.execute_one(
                "SELECT pg_database_size(current_database()) / 1024.0 / 1024.0 as size_mb"
            )
            if size_result:
                db_size_mb = round(size_result['size_mb'], 2)
        except Exception:
            pass  # Ignore if we don't have permission
        
        logger.info(
            f"Stats: {total_photos} photos, {total_faces} faces, "
            f"{primary_faces} primary, {len(event_tags)} event tags"
        )
        
        return StatsResponse(
            total_photos=total_photos,
            total_faces=total_faces,
            primary_faces=primary_faces,
            event_tags=event_tags,
            database_size_mb=db_size_mb
        )
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        # Return empty stats on error
        return StatsResponse(
            total_photos=0,
            total_faces=0,
            primary_faces=0,
            event_tags=[],
            database_size_mb=None
        )
