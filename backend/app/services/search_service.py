"""Search service for finding similar faces"""
import logging
from typing import List, Optional
import time

from ..core.db import get_db
from ..core.config import settings
from ..services.face_embedder import face_embedder
from ..services.face_detector import face_detector
from ..services.image_store import image_store
from ..models.schemas import SearchResult

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching similar faces using vector similarity"""
    
    def __init__(self):
        self.db = get_db()
    
    def search_similar_faces(
        self,
        query_embedding: List[float],
        top_k: int = 30,
        threshold: float = 0.6,
        event_tag: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search for similar faces using cosine similarity
        
        Args:
            query_embedding: Query face embedding vector
            top_k: Maximum number of results to return
            threshold: Minimum similarity threshold (0 to 1)
            event_tag: Optional filter by event tag
            
        Returns:
            List of SearchResult objects sorted by similarity (descending)
        """
        # Build query with optional event_tag filter
        query = """
            SELECT 
                p.id as photo_id,
                p.path,
                p.width,
                p.height,
                p.event_tag,
                1 - (f.embedding <=> %s::vector) as similarity
            FROM faces f
            JOIN photos p ON f.photo_id = p.id
            WHERE f.is_primary = true
        """
        
        params = [query_embedding]
        
        if event_tag:
            query += " AND p.event_tag = %s"
            params.append(event_tag)
        
        # Apply similarity threshold
        query += " AND (1 - (f.embedding <=> %s::vector)) >= %s"
        params.extend([query_embedding, threshold])
        
        # Order by similarity and limit
        query += " ORDER BY f.embedding <=> %s::vector LIMIT %s"
        params.extend([query_embedding, top_k])
        
        try:
            results = self.db.execute(query, tuple(params))
            
            search_results = []
            for row in results:
                image_url = image_store.get_image_url(row['path'])
                search_results.append(
                    SearchResult(
                        photo_id=str(row['photo_id']),
                        image_url=image_url,
                        similarity=float(row['similarity']),
                        event_tag=row['event_tag'],
                        width=row['width'],
                        height=row['height']
                    )
                )
            
            logger.info(f"Found {len(search_results)} similar faces")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def search_by_image(
        self,
        image_data: bytes,
        top_k: int = 30,
        threshold: float = 0.6,
        event_tag: Optional[str] = None
    ) -> tuple[List[SearchResult], float]:
        """
        Search for similar faces by uploading a query image
        
        Args:
            image_data: Raw image bytes
            top_k: Maximum number of results
            threshold: Minimum similarity threshold
            event_tag: Optional filter by event tag
            
        Returns:
            Tuple of (search results, query time in ms, face detected flag)
        """
        from ..utils.image_io import load_image_from_bytes
        
        start_time = time.time()
        
        # Load image
        image, _, _ = load_image_from_bytes(image_data)
        
        # Detect face and get embedding
        embedding = face_embedder.get_embedding(image)
        
        query_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if embedding is None:
            logger.warning("No face detected in query image")
            return [], query_time, False
        
        # Search similar faces
        results = self.search_similar_faces(
            embedding.tolist(),
            top_k=top_k,
            threshold=threshold,
            event_tag=event_tag
        )
        
        return results, query_time, True


# Global instance
search_service = SearchService()
