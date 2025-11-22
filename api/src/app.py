"""FastAPI application entry point for dual deployment (ECS/Lambda)."""

# Load environment configuration first, before any other imports
from env_loader import load_environment_config

# Import all other modules
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from config import get_settings
from routers import workflows, runs, health
from middleware import RateLimitMiddleware, LoggingMiddleware
from exceptions import LandingAPIException

# Load environment configuration at the beginning of execution
load_environment_config()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Get settings
settings = get_settings()

# Determine root path from environment
# PATH_PREFIX tells FastAPI where the app is mounted (e.g., "/dev/v1")
root_path = os.getenv("PATH_PREFIX", "")
if root_path:
    logger.info(f"PATH_PREFIX detected, setting root_path to: {root_path}")
else:
    logger.info("No PATH_PREFIX set, running at root path")

# Create FastAPI app
app = FastAPI(
    title="Landing API",
    description="Backend API for the Credomax landing site",
    version="0.1.0",
    docs_url="/docs",  # Always enable docs for development
    redoc_url="/redoc",  # Always enable redoc for development
    root_path=root_path,  # This tells FastAPI about the path prefix for URL generation
)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, rate_limit=settings.rate_limit)

# CORS middleware
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

# Trusted host middleware for production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts
    )

# Include routers
app.include_router(health.router)
app.include_router(workflows.router, prefix="/workflows")
app.include_router(runs.router, prefix="/runs")


@app.exception_handler(LandingAPIException)
async def landing_exception_handler(request: Request, exc: LandingAPIException):
    """Handle API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }
        }
    )


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Landing API starting up", version="0.1.0")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Landing API shutting down")


@app.get("/")
async def root():
    """Root endpoint."""
    # When deployed via API Gateway, docs are accessible at the root_path + /docs
    docs_url = None
    if settings.debug:
        docs_url = f"{root_path}/docs" if root_path else "/docs"
    
    return {
        "name": "Landing API",
        "version": "0.1.0",
        "description": "Backend API for the Credomax landing site",
        "docs_url": docs_url,
        "root_path": root_path if root_path else None  # Show deployment context
    }
