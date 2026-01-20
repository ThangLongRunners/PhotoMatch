from typing import List, Tuple, Optional
import numpy as np


def compute_bbox_area(bbox: List[float]) -> float:
    """
    Compute area of bounding box
    
    Args:
        bbox: [x1, y1, x2, y2]
        
    Returns:
        Area in pixels
    """
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    return width * height


def select_largest_face(faces: List[dict]) -> Optional[dict]:
    """
    Select the face with largest bounding box area
    
    Args:
        faces: List of face dictionaries with 'bbox' key
        
    Returns:
        Face with largest bbox, or None if no faces
    """
    if not faces:
        return None
    
    largest_face = None
    largest_area = 0
    
    for face in faces:
        area = compute_bbox_area(face['bbox'])
        if area > largest_area:
            largest_area = area
            largest_face = face
    
    return largest_face


def select_top_n_faces(faces: List[dict], n: int = 3) -> List[dict]:
    """
    Select the top N largest faces by bounding box area
    
    Args:
        faces: List of face dictionaries with 'bbox' key
        n: Number of largest faces to return (default: 3)
        
    Returns:
        List of up to N faces sorted by area (largest first)
    """
    if not faces:
        return []
    
    # Compute area for each face and sort by area (descending)
    faces_with_area = [(face, compute_bbox_area(face['bbox'])) for face in faces]
    faces_with_area.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N faces
    return [face for face, area in faces_with_area[:n]]


def normalize_bbox(bbox: List[float]) -> Tuple[int, int, int, int]:
    """
    Normalize bounding box to integers
    
    Args:
        bbox: [x1, y1, x2, y2]
        
    Returns:
        Tuple of (x1, y1, x2, y2) as integers
    """
    x1, y1, x2, y2 = bbox
    return int(x1), int(y1), int(x2), int(y2)
