import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self._connection = psycopg.connect(
                self.connection_string,
                row_factory=dict_row
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            logger.info("Database connection closed")
    
    @contextmanager
    def get_cursor(self) -> Generator:
        """Get a database cursor"""
        if not self._connection:
            self.connect()
        
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def execute(self, query: str, params: tuple = None):
        """Execute a query"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall() if cursor.description else None
    
    def execute_one(self, query: str, params: tuple = None):
        """Execute a query and return one result"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone() if cursor.description else None


# Global database instance
db = Database(settings.database_url)


def get_db() -> Database:
    """Dependency for getting database instance"""
    return db
