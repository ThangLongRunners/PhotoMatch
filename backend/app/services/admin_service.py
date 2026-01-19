"""Admin service for managing photos"""
import logging
from typing import List, Optional, Dict
from pathlib import Path
import uuid
from datetime import datetime

from ..core.db import db
from .image_store import image_store
from .ingest_service import IngestService

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin operations"""
    
    def __init__(self):
        self.ingest_service = IngestService()
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Simple authentication check
        For production, use proper password hashing!
        """
        return username == "admin" and password == "admin"
    
    def get_all_photos(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all photos from database"""
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    p.id,
                    p.path,
                    p.event_tag,
                    p.width,
                    p.height,
                    p.created_at,
                    COUNT(f.id) as face_count
                FROM photos p
                LEFT JOIN faces f ON p.id = f.photo_id
                GROUP BY p.id, p.path, p.event_tag, p.width, p.height, p.created_at
                ORDER BY p.created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            photos = cur.fetchall()
            
            # Convert to list of dicts and add image URLs
            result = []
            for photo in photos:
                photo_dict = dict(photo)
                # Convert UUID to string
                photo_dict['id'] = str(photo_dict['id'])
                photo_dict['image_url'] = image_store.get_image_url(photo_dict['path'])
                result.append(photo_dict)
            
            return result
    
    def get_photo_by_id(self, photo_id: str) -> Optional[Dict]:
        """Get single photo by ID"""
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    p.id,
                    p.path,
                    p.event_tag,
                    p.width,
                    p.height,
                    p.created_at
                FROM photos p
                WHERE p.id = %s
            """, (photo_id,))
            
            photo = cur.fetchone()
            if photo:
                photo_dict = dict(photo)
                # Convert UUID to string
                photo_dict['id'] = str(photo_dict['id'])
                photo_dict['image_url'] = image_store.get_image_url(photo_dict['path'])
                return photo_dict
            return None
            return None
    
    def delete_photo(self, photo_id: str) -> bool:
        """Delete photo and its faces from database"""
        with db.get_cursor() as cur:
            # First delete associated faces
            cur.execute("DELETE FROM faces WHERE photo_id = %s", (photo_id,))
            
            # Then delete photo
            cur.execute("DELETE FROM photos WHERE id = %s", (photo_id,))
            
            return cur.rowcount > 0
    
    def update_photo_tag(self, photo_id: str, event_tag: Optional[str]) -> bool:
        """Update photo event tag"""
        with db.get_cursor() as cur:
            cur.execute("""
                UPDATE photos 
                SET event_tag = %s 
                WHERE id = %s
            """, (event_tag, photo_id))
            
            return cur.rowcount > 0
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with db.get_cursor() as cur:
            # Total photos
            cur.execute("SELECT COUNT(*) as count FROM photos")
            total_photos = cur.fetchone()['count']
            
            # Total faces
            cur.execute("SELECT COUNT(*) as count FROM faces")
            total_faces = cur.fetchone()['count']
            
            # Event tags
            cur.execute("""
                SELECT DISTINCT event_tag 
                FROM photos 
                WHERE event_tag IS NOT NULL
                ORDER BY event_tag
            """)
            event_tags = [row['event_tag'] for row in cur.fetchall()]
            
            return {
                'total_photos': total_photos,
                'total_faces': total_faces,
                'event_tags': event_tags
            }
    
    def upload_image(
        self,
        file_content: bytes,
        filename: str,
        event_tag: Optional[str] = None
    ) -> Dict:
        """
        Upload and process a new image
        
        Args:
            file_content: Image file content in bytes
            filename: Original filename
            event_tag: Optional event tag
            
        Returns:
            Dict with upload result
        """
        try:
            # Create unique filename to avoid conflicts
            unique_filename = f"{uuid.uuid4()}_{filename}"
            relative_path = f"uploads/{unique_filename}"
            
            # Prepare destination in permanent storage
            dest_path = Path(image_store.base_path) / relative_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file directly to permanent storage
            with open(dest_path, 'wb') as f:
                f.write(file_content)
            
            # Process with ingest service (using permanent path)
            success, message = self.ingest_service.ingest_image(
                str(dest_path),
                event_tag=event_tag
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'Image uploaded and processed successfully',
                    'path': relative_path
                }
            else:
                # Clean up file if processing failed
                if dest_path.exists():
                    dest_path.unlink()
                
                return {
                    'success': False,
                    'message': f'Failed to process image: {message}'
                }
                
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            return {
                'success': False,
                'message': f'Upload error: {str(e)}'
            }


# Global instance
admin_service = AdminService()
