"""Workflow management service."""

import structlog
from typing import List, Dict, Any
from datetime import datetime

from legacy_common_all.models import Workflow
from legacy_common_backend.dynamodb import DynamoDBStateManager, DynamoDBConfig
from config import get_settings
from exceptions import WorkflowNotFoundError

logger = structlog.get_logger()


class WorkflowService:
    """Service for managing workflows."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_config = DynamoDBConfig(
            region=self.settings.aws_region,
            access_key_id=self.settings.aws_access_key_id,
            secret_access_key=self.settings.aws_secret_access_key
        )
        self.db_manager = DynamoDBStateManager(self.db_config)
    
    async def create_workflow(
        self,
        name: str,
        description: str,
        definition: Dict[str, Any],
        tags: List[str],
        created_by: str
    ) -> Workflow:
        """Create a new workflow."""
        
        workflow = Workflow(
            name=name,
            description=description,
            definition=definition,
            tags=tags,
            created_by=created_by
        )
        
        # Save to DynamoDB
        await self.db_manager.create_workflow(workflow.dict())
        
        logger.info("Workflow created", workflow_id=workflow.id, name=name)
        return workflow
    
    async def get_workflow(self, workflow_id: str, user_id: str) -> Workflow:
        """Get a workflow by ID."""
        
        item = await self.db_manager.get_workflow(workflow_id)
        
        if not item:
            raise WorkflowNotFoundError(workflow_id)
        
        workflow = Workflow(**item)
        
        # Check ownership
        if workflow.created_by != user_id:
            raise WorkflowNotFoundError(workflow_id)
        
        return workflow
    
    async def list_workflows(self, created_by: str) -> List[Workflow]:
        """List workflows for a user."""
        
        items = await self.db_manager.list_workflows()
        
        # Filter by user (since the backend doesn't have user filtering yet)
        user_workflows = [item for item in items if item.get("created_by") == created_by]
        
        return [Workflow(**item) for item in user_workflows]
