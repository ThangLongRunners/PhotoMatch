from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/photomatch",
        env="DATABASE_URL"
    )
    
    # Storage
    images_folder: str = Field(default="data/images", env="IMAGES_FOLDER")
    static_mount_path: str = "/static"
    
    # Face detection/embedding
    face_detection_backend: str = "retinaface"
    embedding_model: str = "buffalo_l"
    embedding_dim: int = 512
    
    # Search
    default_top_k: int = 30
    default_similarity_threshold: float = 0.6
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
