"""Placeholder workflows router for the Landing API.

The original workflow management endpoints from the previous project are not
used in this repository. This module is kept as a lightweight placeholder to
avoid breaking imports and can be repurposed for future Landing API
functionality.
"""

from fastapi import APIRouter


router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("")
async def list_workflows_placeholder():
    """Placeholder workflows endpoint (not implemented)."""

    return {"message": "Workflows API is not implemented for the Landing API."}
