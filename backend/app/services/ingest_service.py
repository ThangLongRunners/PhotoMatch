"""Ingest service for processing and storing images with face embeddings"""
import logging
from typing import Optional, Tuple
from pathlib import Path
import uuid

from ..core.db import get_db
from ..utils.image_io import load_image, compute_sha1, get_supported_images
from ..utils.bbox import normalize_bbox
from .face_embedder import face_embedder
from .face_detector import face_detector
from .image_store import image_store

logger = logging.getLogger(__name__)


class IngestService:
    """Service for ingesting images and extracting face embeddings"""
    
    def __init__(self):
        self.db = get_db()
    
    def check_duplicate(self, sha1_hash: str) -> bool:
        """
        Check if image with this hash already exists in database
        
        Args:
            sha1_hash: SHA1 hash of image
            
        Returns:
            True if duplicate exists
        """
        result = self.db.execute_one(
            "SELECT id FROM photos WHERE sha1 = %s",
            (sha1_hash,)
        )
        return result is not None
    
    def ingest_image(
        self,
        file_path: str,
        event_tag: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Ingest a single image: detect face, compute embedding, store in DB
        
        Args:
            file_path: Path to image file
            event_tag: Optional event tag for grouping
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Compute hash
            sha1_hash = compute_sha1(file_path)
            
            # Check for duplicates
            if self.check_duplicate(sha1_hash):
                logger.info(f"Skipping duplicate: {file_path}")
                return False, "duplicate"
            
            # Load image
            image, width, height = load_image(file_path)
            
            # Detect largest face and get embedding
            face = face_detector.detect_largest_face(image)
            
            if face is None:
                logger.warning(f"No face detected in: {file_path}")
                return False, "no_face"
            
            # Get normalized embedding
            embedding = face_embedder.normalize_embedding(face['embedding'])
            
            # Get normalized bbox
            x1, y1, x2, y2 = normalize_bbox(face['bbox'])
            
            # Get relative path for storage
            relative_path = image_store.get_relative_path(file_path)
            
            # Insert photo record
            photo_id = str(uuid.uuid4())
            self.db.execute(
                """
                INSERT INTO photos (id, path, sha1, width, height, event_tag)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (photo_id, relative_path, sha1_hash, width, height, event_tag)
            )
            
            # Insert face record with embedding
            face_id = str(uuid.uuid4())
            # Convert embedding to list for pgvector
            embedding_list = embedding.tolist()
            
            self.db.execute(
                """
                INSERT INTO faces (id, photo_id, x1, y1, x2, y2, embedding, is_primary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (face_id, photo_id, x1, y1, x2, y2, embedding_list, True)
            )
            
            logger.info(f"Successfully ingested: {file_path} (photo_id={photo_id})")
            return True, "success"
            
        except Exception as e:
            logger.error(f"Failed to ingest {file_path}: {e}")
            return False, str(e)
    
    def ingest_folder(
        self,
        folder_path: str,
        recursive: bool = True,
        event_tag: Optional[str] = None
    ) -> dict:
        """
        Ingest all images from a folder
        
        Args:
            folder_path: Path to folder containing images
            recursive: Whether to search recursively
            event_tag: Optional event tag for grouping
            
        Returns:
            Dictionary with counts: processed, skipped, errors
        """
        # Initialize face detector before processing
        face_detector.initialize()
        
        # Get all image files
        try:
            image_files = get_supported_images(folder_path, recursive)
        except Exception as e:
            logger.error(f"Failed to scan folder {folder_path}: {e}")
            return {"processed": 0, "skipped": 0, "errors": 1}
        
        logger.info(f"Found {len(image_files)} images in {folder_path}")
        
        stats = {
            "processed": 0,
            "skipped": 0,
            "errors": 0
        }
        
        for img_path in image_files:
            success, message = self.ingest_image(img_path, event_tag)
            
            if success:
                stats["processed"] += 1
            elif message == "duplicate" or message == "no_face":
                stats["skipped"] += 1
            else:
                stats["errors"] += 1
        
        logger.info(
            f"Ingest complete: processed={stats['processed']}, "
            f"skipped={stats['skipped']}, errors={stats['errors']}"
        )
        
        return stats


# Global instance
ingest_service = IngestService()
