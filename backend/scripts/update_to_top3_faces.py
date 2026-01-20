"""
Migration script to update existing database to keep only top 3 largest faces per photo.
This script will:
1. For each photo with more than 3 faces, keep only the 3 largest faces
2. For photos with 3 or fewer faces, keep all faces
3. Update is_primary flag: only the largest face is marked as primary
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import get_db
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_face_area(x1: int, y1: int, x2: int, y2: int) -> int:
    """Compute area of face bounding box"""
    return (x2 - x1) * (y2 - y1)


def update_database():
    """Update database to keep only top 3 largest faces per photo"""
    db = get_db()
    
    try:
        # Get all photos with their faces
        logger.info("Fetching all photos with faces...")
        photos = db.execute(
            """
            SELECT DISTINCT p.id, p.path, p.created_at
            FROM photos p
            INNER JOIN faces f ON f.photo_id = p.id
            ORDER BY p.created_at
            """
        )
        
        if not photos:
            logger.info("No photos found in database")
            return
        
        logger.info(f"Found {len(photos)} photos with faces")
        
        total_faces_before = 0
        total_faces_after = 0
        photos_updated = 0
        
        for photo in photos:
            photo_id = photo['id']
            photo_path = photo['path']
            
            # Get all faces for this photo
            faces = db.execute(
                """
                SELECT id, x1, y1, x2, y2
                FROM faces
                WHERE photo_id = %s
                ORDER BY (x2 - x1) * (y2 - y1) DESC
                """,
                (photo_id,)
            )
            
            num_faces = len(faces)
            total_faces_before += num_faces
            
            if num_faces <= 3:
                # Keep all faces, but ensure only the largest is primary
                if num_faces > 0:
                    # Set all faces to non-primary first
                    db.execute(
                        """
                        UPDATE faces
                        SET is_primary = false
                        WHERE photo_id = %s
                        """,
                        (photo_id,)
                    )
                    
                    # Set the largest face as primary
                    db.execute(
                        """
                        UPDATE faces
                        SET is_primary = true
                        WHERE id = %s
                        """,
                        (faces[0]['id'],)
                    )
                
                total_faces_after += num_faces
                logger.debug(f"Photo {photo_path}: kept all {num_faces} faces")
            else:
                # Keep only top 3 faces
                faces_to_keep = faces[:3]
                faces_to_delete = faces[3:]
                
                # Delete faces beyond top 3
                for face in faces_to_delete:
                    db.execute(
                        "DELETE FROM faces WHERE id = %s",
                        (face['id'],)
                    )
                
                # Set all remaining faces to non-primary first
                db.execute(
                    """
                    UPDATE faces
                    SET is_primary = false
                    WHERE photo_id = %s
                    """,
                    (photo_id,)
                )
                
                # Set the largest face as primary
                db.execute(
                    """
                    UPDATE faces
                    SET is_primary = true
                    WHERE id = %s
                    """,
                    (faces_to_keep[0]['id'],)
                )
                
                total_faces_after += len(faces_to_keep)
                photos_updated += 1
                logger.info(
                    f"Photo {photo_path}: kept top 3 faces out of {num_faces} "
                    f"(deleted {len(faces_to_delete)} faces)"
                )
        
        logger.info("=" * 60)
        logger.info("Migration completed successfully!")
        logger.info(f"Total photos processed: {len(photos)}")
        logger.info(f"Photos updated (had >3 faces): {photos_updated}")
        logger.info(f"Total faces before: {total_faces_before}")
        logger.info(f"Total faces after: {total_faces_after}")
        logger.info(f"Faces removed: {total_faces_before - total_faces_after}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    logger.info("Starting migration: Update to top 3 largest faces per photo")
    logger.info("=" * 60)
    
    try:
        update_database()
    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        sys.exit(1)
    
    logger.info("Migration script completed successfully")
