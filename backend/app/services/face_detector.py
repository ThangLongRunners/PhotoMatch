"""Face detection service using InsightFace"""
import logging
from typing import List, Optional, Dict
import numpy as np

from ..core.config import settings
from ..utils.bbox import select_largest_face, normalize_bbox

logger = logging.getLogger(__name__)


class FaceDetector:
    """Detects faces in images using InsightFace"""
    
    def __init__(self):
        self.app = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the face detection model"""
        if self._initialized:
            return
        
        try:
            # Import InsightFace only when needed (lazy loading)
            from insightface.app import FaceAnalysis
            
            logger.info(f"Initializing face detector with model: {settings.embedding_model}")
            self.app = FaceAnalysis(
                name=settings.embedding_model,
                allowed_modules=['detection', 'recognition']
            )
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            self._initialized = True
            logger.info("Face detector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize face detector: {e}")
            raise
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Detect all faces in an image
        
        Args:
            image: RGB image as numpy array
            
        Returns:
            List of face dictionaries with keys:
            - bbox: [x1, y1, x2, y2]
            - embedding: face embedding vector
            - det_score: detection confidence score
        """
        if not self._initialized:
            self.initialize()
        
        try:
            # InsightFace expects BGR
            image_bgr = image[:, :, ::-1]
            
            faces = self.app.get(image_bgr)
            
            result = []
            for face in faces:
                result.append({
                    'bbox': face.bbox.tolist(),
                    'embedding': face.embedding,
                    'det_score': float(face.det_score)
                })
            
            logger.debug(f"Detected {len(result)} faces")
            return result
            
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            raise
    
    def detect_largest_face(self, image: np.ndarray) -> Optional[Dict]:
        """
        Detect all faces and return only the largest one
        
        Args:
            image: RGB image as numpy array
            
        Returns:
            Face dictionary with largest bbox, or None if no faces detected
        """
        faces = self.detect_faces(image)
        
        if not faces:
            logger.warning("No faces detected in image")
            return None
        
        largest_face = select_largest_face(faces)
        
        if largest_face:
            x1, y1, x2, y2 = normalize_bbox(largest_face['bbox'])
            logger.info(f"Selected largest face: bbox=({x1}, {y1}, {x2}, {y2})")
        
        return largest_face


# Global instance
face_detector = FaceDetector()
