"""
Meeting Notes Intelligence Suite - FastAPI Backend
Main application entry point for AWS App Runner deployment.
"""
import os
import sys
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Critical: Validate environment variables on startup (fail-fast pattern)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable is required")
    raise ValueError("GEMINI_API_KEY environment variable required")

# Import routers after environment validation
from routers import transcribe, refine, summarize
from models import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    logger.info("=" * 50)
    logger.info("Meeting Notes Intelligence Suite Starting...")
    logger.info(f"Environment: {os.environ.get('ENVIRONMENT', 'production')}")
    logger.info(f"Port: {os.environ.get('PORT', '8000')}")
    logger.info("Gemini API Key: configured ✓")
    logger.info("=" * 50)
    
    yield
    
    # Shutdown
    logger.info("=" * 50)
    logger.info("Meeting Notes Intelligence Suite Shutting Down...")
    logger.info("Cleanup completed successfully")
    logger.info("=" * 50)


# Create FastAPI application
app = FastAPI(
    title="Meeting Notes Intelligence Suite",
    description="""
    A powerful API for transcribing, refining, and summarizing meeting audio using Google Gemini AI.
    
    ## Features
    
    * **Transcribe** - Upload audio files and get verbatim transcriptions with speaker identification
    * **Refine** - Map speaker placeholders to real names with grammar corrections
    * **Summarize** - Generate structured Markdown meeting summaries
    
    ## AWS App Runner Ready
    
    This API is designed for deployment on AWS App Runner using the managed Python 3.11 runtime.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS middleware (development mode - allows all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transcribe.router, tags=["Transcription"])
app.include_router(refine.router, tags=["Refinement"])
app.include_router(summarize.router, tags=["Summarization"])


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent response format."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    logger.error(f"Validation error: {str(exc)} - Path: {request.url.path}")
    return JSONResponse(
        status_code=400,
        content={
            "error": True,
            "status_code": 400,
            "detail": str(exc),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)} - Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "detail": "An unexpected error occurred. Please try again later.",
            "path": str(request.url.path)
        }
    )


# Health check endpoints
@app.get("/", response_model=dict, summary="Simple Health Check")
async def health():
    """
    Simple health check endpoint for AWS App Runner.
    
    Returns a minimal response to confirm the service is running.
    This endpoint is called frequently by the load balancer.
    """
    return {"status": "ok"}


@app.get("/health", response_model=HealthResponse, summary="Detailed Health Check")
async def health_detailed():
    """
    Detailed health check endpoint with service information.
    
    Returns comprehensive information about the service status,
    version, and current timestamp.
    """
    return HealthResponse(
        status="healthy",
        service="Meeting Notes Intelligence Suite",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        environment=os.environ.get("ENVIRONMENT", "production"),
        gemini_configured=bool(GEMINI_API_KEY)
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.environ.get("ENVIRONMENT") == "development"
    )
