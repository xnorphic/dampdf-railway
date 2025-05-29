import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "DamPDF API"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Railway automatically provides PORT
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Railway provides REDIS_URL when Redis service is added
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # CORS origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-frontend-domain.com",
    ]
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    
    # File processing settings
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", 50))
    TEMP_FILE_EXPIRE_HOURS: int = int(os.getenv("TEMP_FILE_EXPIRE_HOURS", 1))
    PROCESSED_FILE_EXPIRE_HOURS: int = int(os.getenv("PROCESSED_FILE_EXPIRE_HOURS", 24))
    
    class Config:
        env_file = ".env"

settings = Settings()
