"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from pathlib import Path
import logging

from .core.config import settings
from .core.db import db
from .api import routes_health, routes_ingest, routes_search, routes_admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Custom StaticFiles with CORS headers
class CORSStaticFiles(StaticFiles):
    async def __call__(self, scope, receive, send):
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add CORS headers to all static file responses
                headers = list(message.get("headers", []))
                headers.append((b"access-control-allow-origin", b"*"))
                headers.append((b"access-control-allow-methods", b"GET, OPTIONS"))
                headers.append((b"access-control-allow-headers", b"*"))
                message["headers"] = headers
            await send(message)
        
        await super().__call__(scope, receive, send_wrapper)


# Create FastAPI app
app = FastAPI(
    title="PhotoMatch API",
    description="Face image search application using pgvector and InsightFace",
    version="1.0.0"
)

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers with /api prefix
app.include_router(routes_health.router, prefix="/api", tags=["health"])
app.include_router(routes_ingest.router, prefix="/api", tags=["ingest"])
app.include_router(routes_search.router, prefix="/api", tags=["search"])
app.include_router(routes_admin.router, prefix="/api", tags=["admin"])

# Mount static files for serving images with CORS support
images_path = Path(settings.images_folder)
images_path.mkdir(parents=True, exist_ok=True)

app.mount(
    settings.static_mount_path,
    CORSStaticFiles(directory=str(images_path)),
    name="static"
)

logger.info(f"Static files mounted at {settings.static_mount_path} -> {images_path}")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting PhotoMatch API")
    
    # Connect to database
    try:
        db.connect()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down PhotoMatch API")
    db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
