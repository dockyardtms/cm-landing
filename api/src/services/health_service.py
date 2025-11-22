"""Simplified health check service for the Landing API.

This stub avoids dependencies on the old legacy health helpers and only
reports basic API health.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class HealthResult:
    healthy: bool
    checks: Dict[str, str]


class HealthService:
    """Service for checking basic system health."""

    async def check_basic_health(self) -> HealthResult:
        """Basic health check - API availability only."""

        return HealthResult(healthy=True, checks={"api": "OK"})

    async def check_detailed_health(self) -> HealthResult:
        """Detailed health check - currently same as basic for Landing API."""

        return await self.check_basic_health()
