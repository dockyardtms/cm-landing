"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from config import get_settings
from routers import workflows, runs, health, contact
from middleware import RateLimitMiddleware, LoggingMiddleware
from exceptions import LandingAPIException

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

# Create FastAPI app
app = FastAPI(
    title="Landing API",
    description="Backend API for the Credomax landing site",
    version="0.1.0",
    docs_url="/docs",  # Always enable docs for development
    redoc_url="/redoc",  # Always enable redoc for development
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
app.include_router(workflows.router, prefix="/v1")
app.include_router(runs.router, prefix="/v1")
app.include_router(contact.router, prefix="/v1")


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
    return {
        "name": "Landing API",
        "version": "0.1.0",
        "description": "Backend API for the Credomax landing site",
        "docs_url": "/docs" if settings.debug else None
    }
