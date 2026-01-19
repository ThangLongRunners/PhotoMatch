import hashlib
from pathlib import Path
from PIL import Image
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def compute_sha1(file_path: str) -> str:
    """Compute SHA1 hash of a file"""
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    return sha1.hexdigest()


def load_image(file_path: str) -> Tuple[np.ndarray, int, int]:
    """
    Load image from file and return as numpy array (RGB) with dimensions
    
    Returns:
        Tuple of (image_array, width, height)
    """
    try:
        img = Image.open(file_path)
        img = img.convert('RGB')
        width, height = img.size
        img_array = np.array(img)
        return img_array, width, height
    except Exception as e:
        logger.error(f"Failed to load image {file_path}: {e}")
        raise


def load_image_from_bytes(image_bytes: bytes) -> Tuple[np.ndarray, int, int]:
    """
    Load image from bytes and return as numpy array (RGB) with dimensions
    
    Returns:
        Tuple of (image_array, width, height)
    """
    try:
        from io import BytesIO
        img = Image.open(BytesIO(image_bytes))
        img = img.convert('RGB')
        width, height = img.size
        img_array = np.array(img)
        return img_array, width, height
    except Exception as e:
        logger.error(f"Failed to load image from bytes: {e}")
        raise


def get_supported_images(folder_path: str, recursive: bool = True) -> list:
    """
    Get all supported image files from a folder
    
    Args:
        folder_path: Path to folder
        recursive: Whether to search recursively
        
    Returns:
        List of image file paths
    """
    supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    folder = Path(folder_path)
    
    if not folder.exists():
        raise ValueError(f"Folder does not exist: {folder_path}")
    
    if recursive:
        files = [
            str(f) for f in folder.rglob('*')
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
    else:
        files = [
            str(f) for f in folder.glob('*')
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
    
    return sorted(files)
