"""
Script to reprocess all existing photos to detect and store top 3 largest faces.
This will:
1. Load each photo from database
2. Re-detect all faces in the image
3. Delete old face records
4. Insert new face records (up to 3 largest faces)
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import get_db
from app.core.config import settings
from app.utils.image_io import load_image
from app.utils.bbox import normalize_bbox, select_top_n_faces
from app.services.face_detector import face_detector
from app.services.face_embedder import face_embedder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def reprocess_all_photos():
    """Reprocess all photos to detect and store top 3 largest faces"""
    db = get_db()
    
    # Initialize face detector
    logger.info("Initializing face detector...")
    face_detector.initialize()
    
    try:
        # Get all photos
        logger.info("Fetching all photos from database...")
        photos = db.execute(
            """
            SELECT id, path, width, height
            FROM photos
            ORDER BY created_at
            """
        )
        
        if not photos:
            logger.info("No photos found in database")
            return
        
        logger.info(f"Found {len(photos)} photos to reprocess")
        
        stats = {
            'processed': 0,
            'failed': 0,
            'no_faces': 0,
            'total_faces_before': 0,
            'total_faces_after': 0,
            'faces_with_multiple': 0
        }
        
        for idx, photo in enumerate(photos, 1):
            photo_id = photo['id']
            photo_path = photo['path']
            
            try:
                # Count existing faces
                existing_faces = db.execute(
                    "SELECT COUNT(*) as count FROM faces WHERE photo_id = %s",
                    (photo_id,)
                )
                faces_before = existing_faces[0]['count'] if existing_faces else 0
                stats['total_faces_before'] += faces_before
                
                # Get full path to image
                # photo_path is relative to images folder
                from pathlib import Path
                full_path = Path(settings.images_folder) / photo_path
                
                if not full_path.exists():
                    logger.error(f"[{idx}/{len(photos)}] Image file not found: {full_path}")
                    stats['failed'] += 1
                    continue
                
                # Load image
                image, width, height = load_image(full_path)
                
                # Detect all faces
                all_faces = face_detector.detect_faces(image)
                
                if not all_faces:
                    logger.warning(f"[{idx}/{len(photos)}] No faces detected: {photo_path}")
                    stats['no_faces'] += 1
                    # Delete old face records
                    db.execute(
                        "DELETE FROM faces WHERE photo_id = %s",
                        (photo_id,)
                    )
                    continue
                
                # Select top 3 largest faces
                top_faces = select_top_n_faces(all_faces, n=3)
                
                # Delete old face records
                db.execute(
                    "DELETE FROM faces WHERE photo_id = %s",
                    (photo_id,)
                )
                
                # Insert new face records
                for face_idx, face in enumerate(top_faces):
                    # Get normalized embedding
                    embedding = face_embedder.normalize_embedding(face['embedding'])
                    
                    # Get normalized bbox
                    x1, y1, x2, y2 = normalize_bbox(face['bbox'])
                    
                    # Convert embedding to list for pgvector
                    embedding_list = embedding.tolist()
                    
                    # First face is primary (largest)
                    is_primary = (face_idx == 0)
                    
                    db.execute(
                        """
                        INSERT INTO faces (photo_id, x1, y1, x2, y2, embedding, is_primary)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (photo_id, x1, y1, x2, y2, embedding_list, is_primary)
                    )
                
                stats['total_faces_after'] += len(top_faces)
                stats['processed'] += 1
                
                if len(top_faces) > 1:
                    stats['faces_with_multiple'] += 1
                
                logger.info(
                    f"[{idx}/{len(photos)}] {photo_path}: "
                    f"detected {len(all_faces)} faces, stored {len(top_faces)} largest"
                )
                
            except Exception as e:
                logger.error(f"[{idx}/{len(photos)}] Failed to reprocess {photo_path}: {e}")
                stats['failed'] += 1
                continue
        
        logger.info("=" * 70)
        logger.info("Reprocessing completed!")
        logger.info(f"Total photos: {len(photos)}")
        logger.info(f"Successfully processed: {stats['processed']}")
        logger.info(f"No faces detected: {stats['no_faces']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Photos with multiple faces (2-3): {stats['faces_with_multiple']}")
        logger.info(f"Total faces before: {stats['total_faces_before']}")
        logger.info(f"Total faces after: {stats['total_faces_after']}")
        logger.info(f"Faces added: {stats['total_faces_after'] - stats['total_faces_before']}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Reprocessing failed: {e}")
        raise


if __name__ == "__main__":
    logger.info("Starting photo reprocessing: Detect and store top 3 largest faces")
    logger.info("=" * 70)
    
    try:
        reprocess_all_photos()
    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        sys.exit(1)
    
    logger.info("Reprocessing script completed successfully")
