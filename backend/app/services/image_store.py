"""Image store service for managing image paths and URLs"""
from pathlib import Path
import shutil
from typing import Optional
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class ImageStore:
    """Manages image storage and URL generation"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.images_folder)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_relative_path(self, absolute_path: str) -> str:
        """
        Convert absolute path to relative path from images folder
        
        Args:
            absolute_path: Absolute file path
            
        Returns:
            Relative path from images folder
        """
        abs_path = Path(absolute_path).resolve()
        try:
            rel_path = abs_path.relative_to(self.base_path.resolve())
            return str(rel_path).replace('\\', '/')
        except ValueError:
            # Path is outside base_path, return absolute
            return str(abs_path).replace('\\', '/')
    
    def get_image_url(self, relative_path: str) -> str:
        """
        Generate URL for accessing image via static files
        
        Args:
            relative_path: Relative path from images folder
            
        Returns:
            URL path for accessing image
        """
        # Ensure forward slashes for URLs
        clean_path = relative_path.replace('\\', '/')
        return f"{settings.static_mount_path}/{clean_path}"
    
    def copy_image(self, source_path: str, dest_relative_path: str) -> str:
        """
        Copy image to storage folder
        
        Args:
            source_path: Source file path
            dest_relative_path: Destination relative path
            
        Returns:
            Absolute path of copied file
        """
        dest_path = self.base_path / dest_relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source_path, dest_path)
        logger.info(f"Copied image to {dest_path}")
        
        return str(dest_path)
    
    def exists(self, relative_path: str) -> bool:
        """Check if image exists in storage"""
        return (self.base_path / relative_path).exists()


# Global instance
image_store = ImageStore()
