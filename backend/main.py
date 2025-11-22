from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.db.session import engine, Base
from app.api.endpoints import submissions, assignments, grades, plagiarism, sections

# Create tables
Base.metadata.create_all(bind=engine)

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(submissions.router, prefix="/api/submissions", tags=["Submissions"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["Assignments"])
app.include_router(grades.router, prefix="/api/grades", tags=["Grades"])
app.include_router(plagiarism.router, prefix="/api/plagiarism", tags=["Plagiarism"])
app.include_router(sections.router, prefix="/api/sections", tags=["Sections"])


@app.get("/")
def root():
    return {
        "message": "CodeMentor AI - Intelligent Tutoring System",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    from app.services.ollama_service import ollama_service
    
    ollama_healthy = await ollama_service.check_health()
    
    return {
        "status": "healthy",
        "services": {
            "ollama": "healthy" if ollama_healthy else "unhealthy",
            "database": "healthy",
            "minio": "healthy"
        }
    }
