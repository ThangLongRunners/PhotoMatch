"""Admin API routes"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List, Optional
import secrets

from ..models.schemas import (
    AdminLoginRequest, AdminLoginResponse,
    AdminPhotoResponse, AdminPhotoListResponse,
    AdminUpdatePhotoRequest, AdminStatsResponse
)
from ..services.admin_service import admin_service

router = APIRouter(prefix="/admin")
security = HTTPBasic()


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    is_valid = admin_service.authenticate(credentials.username, credentials.password)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username


@router.post("/login", response_model=AdminLoginResponse)
async def login(request: AdminLoginRequest):
    """Admin login endpoint"""
    is_valid = admin_service.authenticate(request.username, request.password)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # In production, generate a real JWT token
    token = secrets.token_urlsafe(32)
    
    return AdminLoginResponse(
        success=True,
        token=token,
        username=request.username
    )


@router.get("/photos", response_model=AdminPhotoListResponse)
async def get_photos(
    limit: int = 100,
    offset: int = 0,
    admin: str = Depends(verify_admin)
):
    """Get all photos with pagination"""
    try:
        photos = admin_service.get_all_photos(limit=limit, offset=offset)
        stats = admin_service.get_stats()
        
        return AdminPhotoListResponse(
            photos=photos,
            total=stats['total_photos'],
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve photos: {str(e)}"
        )


@router.get("/photos/{photo_id}", response_model=AdminPhotoResponse)
async def get_photo(
    photo_id: str,
    admin: str = Depends(verify_admin)
):
    """Get single photo by ID"""
    photo = admin_service.get_photo_by_id(photo_id)
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo {photo_id} not found"
        )
    
    return photo


@router.put("/photos/{photo_id}", response_model=AdminPhotoResponse)
async def update_photo(
    photo_id: str,
    request: AdminUpdatePhotoRequest,
    admin: str = Depends(verify_admin)
):
    """Update photo event tag"""
    success = admin_service.update_photo_tag(photo_id, request.event_tag)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo {photo_id} not found"
        )
    
    photo = admin_service.get_photo_by_id(photo_id)
    return photo


@router.delete("/photos/{photo_id}")
async def delete_photo(
    photo_id: str,
    admin: str = Depends(verify_admin)
):
    """Delete photo and its faces"""
    success = admin_service.delete_photo(photo_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo {photo_id} not found"
        )
    
    return {"success": True, "message": f"Photo {photo_id} deleted"}


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(admin: str = Depends(verify_admin)):
    """Get database statistics"""
    try:
        stats = admin_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    event_tag: Optional[str] = Form(None),
    admin: str = Depends(verify_admin)
):
    """Upload a new image"""
    try:
        # Check file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Read file content
        content = await file.read()
        
        # Process upload
        result = admin_service.upload_image(
            file_content=content,
            filename=file.filename,
            event_tag=event_tag
        )
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )
