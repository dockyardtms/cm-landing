"""Authentication and authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from config import get_settings

logger = structlog.get_logger()

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current authenticated user from API key."""
    
    # For MVP, we'll use a simple API key validation
    # In production, you'd want proper JWT tokens or OAuth
    
    api_key = credentials.credentials
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )
    
    # TODO: Implement proper API key validation against database
    # For now, we'll accept any non-empty key and return a user ID
    
    if len(api_key) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Extract user ID from API key (simplified for MVP)
    # In production, you'd look this up in a database
    user_id = f"user_{api_key[:8]}"
    
    logger.info("User authenticated", user_id=user_id)
    
    return user_id


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current user, but don't require authentication."""
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return "anonymous"
