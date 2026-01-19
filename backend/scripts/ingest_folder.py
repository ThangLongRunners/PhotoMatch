"""Script to ingest images from a folder"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ingest_service import ingest_service
from app.core.db import db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run folder ingest from command line"""
    if len(sys.argv) < 2:
        print("Usage: python ingest_folder.py <folder_path> [event_tag]")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    event_tag = sys.argv[2] if len(sys.argv) > 2 else None
    
    logger.info(f"Starting ingest: folder={folder_path}, event_tag={event_tag}")
    
    try:
        # Connect to database
        db.connect()
        
        # Run ingest
        stats = ingest_service.ingest_folder(
            folder_path=folder_path,
            recursive=True,
            event_tag=event_tag
        )
        
        logger.info(
            f"Ingest complete: processed={stats['processed']}, "
            f"skipped={stats['skipped']}, errors={stats['errors']}"
        )
        
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
