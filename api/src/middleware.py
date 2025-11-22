"""Custom middleware for the API service."""

import time
import structlog
from typing import Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from exceptions import RateLimitError

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=request.client.host if request.client else None
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, rate_limit: int = 100):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.requests: Dict[str, list] = {}
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Get client identifier (IP address for now)
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not self._check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit of {self.rate_limit} requests per minute exceeded"
                    }
                }
            )
        
        return await call_next(request)
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is within rate limit."""
        current_time = time.time()
        
        # Initialize client request history if not exists
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Remove old requests outside the window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.window_size
        ]
        
        # Check if under limit
        if len(self.requests[client_ip]) >= self.rate_limit:
            return False
        
        # Add current request
        self.requests[client_ip].append(current_time)
        return True
