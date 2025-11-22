"""Custom exceptions for the Landing API service."""

from typing import Optional, Dict, Any


class LandingAPIException(Exception):
    """Base exception for Landing API errors."""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class WorkflowNotFoundError(LandingAPIException):
    """Workflow not found error."""
    
    def __init__(self, workflow_id: str):
        super().__init__(
            status_code=404,
            error_code="WORKFLOW_NOT_FOUND",
            message=f"Workflow {workflow_id} not found"
        )


class RunNotFoundError(LandingAPIException):
    """Run not found error."""
    
    def __init__(self, run_id: str):
        super().__init__(
            status_code=404,
            error_code="RUN_NOT_FOUND",
            message=f"Run {run_id} not found"
        )


class InvalidWorkflowError(LandingAPIException):
    """Invalid workflow definition error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            error_code="INVALID_WORKFLOW",
            message=message,
            details=details
        )


class ConcurrencyLimitError(LandingAPIException):
    """Concurrency limit exceeded error."""
    
    def __init__(self, message: str = "Concurrency limit exceeded"):
        super().__init__(
            status_code=429,
            error_code="CONCURRENCY_LIMIT_EXCEEDED",
            message=message
        )


class RateLimitError(LandingAPIException):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            message=message
        )
