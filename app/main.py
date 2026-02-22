# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, admin, submissions

# Initialize Database Schema (In a real production environment, use Alembic migrations instead)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Dynamic Hierarchical Approval & Intelligent Workflow Automation System API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
# The frontend URL (e.g., Vercel deployment or localhost:3000) must be allowed here
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # Vite default
    "*" # Warning: Change this in production to specific frontend URLs
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin Operations"])
app.include_router(submissions.router, prefix=f"{settings.API_V1_STR}/submissions", tags=["Workflow & Submissions"])

@app.get("/health")
def health_check():
    """Simple health check endpoint for monitoring."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}