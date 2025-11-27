"""Configuration management for the API service."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API configuration settings."""
    
    # API Configuration
    version: str = Field(default="0.1.0", env="VERSION")
    debug: bool = Field(default=False, env="LANDING_API_DEBUG")
    secret_key: str = Field(default="dev-secret-key", env="LANDING_API_SECRET_KEY")
    rate_limit: int = Field(default=100, env="LANDING_API_RATE_LIMIT")
    allowed_hosts: List[str] = Field(default=["*"], env="LANDING_API_ALLOWED_HOSTS")
    cors_origins: Optional[List[str]] = Field(default=None, env="LANDING_API_CORS_ORIGINS")
    
    # AWS Configuration
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    
    # DynamoDB Tables (legacy; not used by the landing form Lambda)
    runs_table: str = Field(default="landing-api-runs", env="LANDING_API_RUNS_TABLE")
    workflows_table: str = Field(default="landing-api-workflows", env="LANDING_API_WORKFLOWS_TABLE")
    context_table: str = Field(default="landing-api-context", env="LANDING_API_CONTEXT_TABLE")
    
    # SQS Configuration (legacy; not used by the landing form Lambda)
    sqs_queue_url: str = Field(default="https://sqs.us-east-1.amazonaws.com/123456789/landing-api-runs-dev", env="LANDING_API_SQS_QUEUE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LANDING_API_LOG_LEVEL")
    
    smtp_host: str = Field(default="localhost", env="LANDING_API_SMTP_HOST")
    smtp_port: int = Field(default=587, env="LANDING_API_SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="LANDING_API_SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="LANDING_API_SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="LANDING_API_SMTP_USE_TLS")
    email_from: str = Field(default="no-reply@example.com", env="LANDING_API_EMAIL_FROM")
    email_to: str = Field(default="contact@example.com", env="LANDING_API_EMAIL_TO")
    
    model_config = {
        "case_sensitive": False,
        "extra": "ignore",
        "validate_by_name": True  # This replaces allow_population_by_field_name
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
