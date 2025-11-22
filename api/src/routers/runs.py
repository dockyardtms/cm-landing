"""Placeholder runs router for the Landing API.

The original run management endpoints from the previous project are not used
in this repository. This module is kept as a lightweight placeholder to avoid
breaking imports and can be repurposed for future Landing API functionality.
"""

from fastapi import APIRouter


router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("")
async def list_runs_placeholder():
    """Placeholder runs endpoint (not implemented)."""

    return {"message": "Runs API is not implemented for the Landing API."}
