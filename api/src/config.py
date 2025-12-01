"""Configuration management for the API service."""

import json
import os
from typing import List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API configuration settings."""
    
    # API Configuration
    version: str = Field(default="0.1.0", env="VERSION")
    debug: bool = Field(default=False, env="LANDING_API_DEBUG")
    rate_limit: int = Field(default=100, env="LANDING_API_RATE_LIMIT")
    allowed_hosts: List[str] = Field(default=["*"], env="LANDING_API_ALLOWED_HOSTS")
    cors_origins: Optional[List[str]] = Field(default=None, env="LANDING_API_CORS_ORIGINS")
    
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
        _settings = _load_settings()
    return _settings


def _load_settings() -> Settings:
    settings = Settings()
    secret_name = os.getenv("LANDING_API_CONFIG_SECRET_NAME")
    if not secret_name:
        print("LANDING_API_CONFIG_SECRET_NAME not set or blank; skipping Secrets Manager config load.")
        return settings

    try:
        session = boto3.session.Session()
        region_name = os.getenv("AWS_REGION") or session.region_name
        client_kwargs = {}
        if region_name:
            client_kwargs["region_name"] = region_name
        client = session.client("secretsmanager", **client_kwargs)

        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString")
        if not secret_string:
            return settings

        secret_data = json.loads(secret_string)

        mapping = {
            "smtp_host": "smtp_host",
            "smtp_port": "smtp_port",
            "smtp_username": "smtp_username",
            "smtp_password": "smtp_password",
            "smtp_use_tls": "smtp_use_tls",
            "email_from": "email_from",
            "email_to": "email_to",
            "LANDING_API_SMTP_HOST": "smtp_host",
            "LANDING_API_SMTP_PORT": "smtp_port",
            "LANDING_API_SMTP_USERNAME": "smtp_username",
            "LANDING_API_SMTP_PASSWORD": "smtp_password",
            "LANDING_API_SMTP_USE_TLS": "smtp_use_tls",
            "LANDING_API_EMAIL_FROM": "email_from",
            "LANDING_API_EMAIL_TO": "email_to",
        }

        updates = {}
        for key, field_name in mapping.items():
            if key in secret_data and secret_data[key] is not None:
                updates[field_name] = secret_data[key]

        if updates:
            data = settings.model_dump()
            data.update(updates)
            settings = Settings.model_validate(data)

    except (BotoCoreError, ClientError, json.JSONDecodeError, Exception):
        return settings

    return settings
