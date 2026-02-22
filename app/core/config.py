# app/core/config.py
from pydantic_settings import BaseSettings

import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "ApproveFlow Enterprise API"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "approveflow"
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # local 
        # return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        SQLALCHEMY_DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "postgresql://postgres:password@localhost:5432/approveflow" # Replace with your actual local credentials
        )

    class Config:
        env_file = ".env"

settings = Settings()