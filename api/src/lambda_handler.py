"""AWS Lambda handler for the FastAPI application using Mangum adapter."""

import logging
from mangum import Mangum
from app import app  # Import the FastAPI instance from app.py (env_loader is imported there)

# Configure logging for CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Lambda handler for the FastAPI application."""
    request_id = getattr(context, 'aws_request_id', 'unknown')
    
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
        
        # Call the Mangum handler
        response = mangum_handler(event, context)
        
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
