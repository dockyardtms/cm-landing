"""AWS Lambda handler for the FastAPI application using Mangum adapter."""

import logging
import os
import sys
from mangum import Mangum

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from .app import app  # Import the FastAPI instance from app.py (env_loader is imported there)

# Configure logging for CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _parse_allowed_origins() -> set[str]:
    """Parse allowed origins from LANDING_API_CORS_ORIGINS.

    Accepts a comma-separated list of origins.
    """
    raw = os.getenv("LANDING_API_CORS_ORIGINS", "")
    return {o.strip() for o in raw.split(",") if o.strip()}


ALLOWED_ORIGINS = _parse_allowed_origins()


def _add_cors_headers(response: dict | None, origin: str | None) -> dict | None:
    """Add CORS headers to the Lambda proxy response if origin is allowed.

    This is a safety net on top of FastAPI's CORSMiddleware to ensure that
    both preflight (OPTIONS) and actual requests include the expected headers
    when invoked via API Gateway.
    """
    if response is None or not isinstance(response, dict):
        return response

    headers = response.get("headers") or {}

    # Normalize header keys to case-insensitive access for existing values
    normalized_headers = {k.lower(): k for k in headers.keys()}

    # Determine if we should set CORS for this origin
    if origin and (not ALLOWED_ORIGINS or origin in ALLOWED_ORIGINS):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        headers["Access-Control-Allow-Methods"] = "OPTIONS,GET,POST,PUT,DELETE"
        headers["Vary"] = "Origin"

    response["headers"] = headers
    return response


def lambda_handler(event, context):
    """Lambda handler for the FastAPI application."""
    request_id = getattr(context, 'aws_request_id', 'unknown')
    origin = None
    
    try:
        # Safely extract key request info for logging
        method = "UNKNOWN"
        path = "UNKNOWN"
        source_ip = "unknown"
        user_agent = "unknown"
        status_code = "unknown"
        
        try:
            method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method", "UNKNOWN"))
            path = event.get("rawPath", event.get("path", "UNKNOWN"))

            # Get real client IP from X-Forwarded-For header (preferred) or fallback to sourceIp
            headers = event.get("headers") or {}
            origin = headers.get("origin") or headers.get("Origin")

            x_forwarded_for = headers.get("x-forwarded-for")
            if x_forwarded_for:
                try:
                    source_ip = x_forwarded_for.split(",")[0].strip()
                except (AttributeError, IndexError):
                    pass
            if source_ip == "unknown":
                try:
                    source_ip = event.get("requestContext", {}).get("http", {}).get("sourceIp", "unknown")
                except (AttributeError, TypeError):
                    pass

            user_agent = headers.get("user-agent", "unknown")
            if user_agent and len(user_agent) > 50:
                user_agent = user_agent[:50] + "..."
        except Exception as e:
            logger.error(f"Error extracting request info: {type(e).__name__}: {str(e)} - RequestID: {request_id}")
        
        # Handle CORS preflight directly to ensure 200 OK for allowed origins
        if method == "OPTIONS":
            preflight_response = {
                "statusCode": 200,
                "headers": {},
                "body": "",
            }
            preflight_response = _add_cors_headers(preflight_response, origin)
            return preflight_response

        # Call the Mangum handler for all non-preflight requests
        response = mangum_handler(event, context)

        # Ensure CORS headers are present on the proxy response
        response = _add_cors_headers(response, origin)
        
        # Single combined log line with request and response info
        try:
            status_code = response.get("statusCode", "unknown") if response else "unknown"
        except Exception as e:
            logger.error(f"Error extracting status code: {type(e).__name__}: {str(e)} - RequestID: {request_id}")

        # We have success logging already in the app
        # logger.info(f"RequestID: {request_id} - {method} {path} - {status_code} - IP: {source_ip} - UserAgent: {user_agent}")

        return response
        
    except Exception as e:
        # Log the main handler error - no need to wrap since 'e' is never null
        logger.error(f"Lambda handler error: {type(e).__name__}: {str(e)} - RequestID: {request_id}")
        # Re-raise the exception so Lambda can handle it properly
        raise


# Create the Mangum handler
mangum_handler = Mangum(app, lifespan="off")

# Export the handler
handler = lambda_handler
