"""Face embedding service"""
import logging
from typing import Optional
import numpy as np

from .face_detector import face_detector
from ..core.config import settings

logger = logging.getLogger(__name__)


class FaceEmbedder:
    """Generates normalized face embeddings"""
    
    def __init__(self):
        self.embedding_dim = settings.embedding_dim
    
    def normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """
        Normalize embedding to unit length (L2 normalization)
        
        Args:
            embedding: Raw embedding vector
            
        Returns:
            Normalized embedding vector
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            logger.warning("Zero norm embedding encountered")
            return embedding
        return embedding / norm
    
    def get_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Get normalized embedding for largest face in image
        
        Args:
            image: RGB image as numpy array
            
        Returns:
            Normalized embedding vector, or None if no face detected
        """
        # Detect largest face (this also computes embedding)
        face = face_detector.detect_largest_face(image)
        
        if face is None:
            return None
        
        # Extract and normalize embedding
        raw_embedding = face['embedding']
        normalized = self.normalize_embedding(raw_embedding)
        
        logger.debug(f"Generated embedding with dim={len(normalized)}")
        
        return normalized
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        # Ensure normalized
        emb1 = self.normalize_embedding(embedding1)
        emb2 = self.normalize_embedding(embedding2)
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2)
        
        return float(similarity)


# Global instance
face_embedder = FaceEmbedder()
