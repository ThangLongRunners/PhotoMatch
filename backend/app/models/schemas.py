from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class IngestFolderRequest(BaseModel):
    path: str = Field(..., description="Path to folder containing images")
    recursive: bool = Field(default=True, description="Recursively process subfolders")
    event_tag: Optional[str] = Field(default=None, description="Optional event tag for grouping")


class IngestFolderResponse(BaseModel):
    processed: int
    skipped: int
    errors: int
    message: str


class SearchResult(BaseModel):
    photo_id: str
    image_url: str
    similarity: float
    event_tag: Optional[str] = None
    width: int
    height: int


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query_time_ms: float
    face_detected: bool = True
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    face_model: str


class StatsResponse(BaseModel):
    total_photos: int
    total_faces: int
    primary_faces: int
    event_tags: List[str]
    database_size_mb: Optional[float] = None


class PhotoItem(BaseModel):
    photo_id: str
    image_url: str
    event_tag: Optional[str] = None
    width: int
    height: int
    created_at: datetime


class PhotoListResponse(BaseModel):
    photos: List[PhotoItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# Admin schemas
class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    token: str
    username: str


class AdminPhotoResponse(BaseModel):
    id: str
    path: str
    image_url: str
    event_tag: Optional[str] = None
    width: int
    height: int
    created_at: datetime
    face_count: Optional[int] = 0


class AdminPhotoListResponse(BaseModel):
    photos: List[AdminPhotoResponse]
    total: int
    limit: int
    offset: int


class AdminUpdatePhotoRequest(BaseModel):
    event_tag: Optional[str] = None


class AdminStatsResponse(BaseModel):
    total_photos: int
    total_faces: int
    event_tags: List[str]
