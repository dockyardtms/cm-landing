"""Run management service."""

import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime

from legacy_common_all.models import Run
from legacy_common_all.types import RunStatus
from legacy_common_backend.dynamodb import DynamoDBStateManager, DynamoDBConfig
from legacy_common_backend.sqs import TypedSQSManager
from config import get_settings
from exceptions import RunNotFoundError, WorkflowNotFoundError

logger = structlog.get_logger()


class RunService:
    """Service for managing workflow runs."""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize DynamoDB
        self.db_config = DynamoDBConfig(
            region=self.settings.aws_region,
            access_key_id=self.settings.aws_access_key_id,
            secret_access_key=self.settings.aws_secret_access_key
        )
        self.db_manager = DynamoDBStateManager(self.db_config)
        
        # Initialize typed SQS manager
        self.sqs_manager = TypedSQSManager(region_name=self.settings.aws_region)
    
    async def create_run(
        self,
        workflow_id: str,
        parameters: Dict[str, Any],
        tags: List[str],
        created_by: str
    ) -> Run:
        """Create and start a new run."""
        
        # Verify workflow exists
        workflow_item = await self.db_manager.get_workflow(workflow_id)
        
        if not workflow_item or workflow_item.get("created_by") != created_by:
            raise WorkflowNotFoundError(workflow_id)
        
        # Create run
        run = Run(
            workflow_id=workflow_id,
            status=RunStatus.PENDING,
            parameters=parameters,
            tags=tags,
            created_by=created_by
        )
        
        # Save to DynamoDB
        await self.db_manager.create_run(run.dict())
        
        # Queue for execution using typed workflow start message
        message_id = self.sqs_manager.send_workflow_start(
            queue_url=self.settings.sqs_queue_url,
            run_id=run.id,
            workflow_id=workflow_id,
            inputs=parameters,
            settings={}
        )
        
        if not message_id:
            raise RuntimeError(f"Failed to queue workflow start message for run {run.id}")
        
        logger.info("Run created and queued", run_id=run.id, workflow_id=workflow_id)
        return run
    
    async def get_run(self, run_id: str, user_id: str) -> Run:
        """Get a run by ID."""
        
        item = await self.db_manager.get_run(run_id)
        
        if not item:
            raise RunNotFoundError(run_id)
        
        run = Run(**item)
        
        # Check ownership
        if run.created_by != user_id:
            raise RunNotFoundError(run_id)
        
        return run
    
    async def list_runs(
        self,
        created_by: str,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Run]:
        """List runs for a user."""
        
        # Get runs (filter by user since backend doesn't have user filtering yet)
        items = await self.db_manager.list_runs(workflow_id=workflow_id, status=status)
        
        # Filter by user
        user_items = [item for item in items if item.get("created_by") == created_by]
        
        runs = [Run(**item) for item in user_items]
        
        # Filter by workflow_id if provided
        if workflow_id:
            runs = [r for r in runs if r.workflow_id == workflow_id]
        
        # Filter by status if provided
        if status:
            runs = [r for r in runs if r.status == status]
        
        return runs
