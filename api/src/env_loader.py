"""Environment configuration loader for the API service."""

import os
from pathlib import Path


def load_environment_config():
    """
    Load environment-specific configuration from config files.
    
    This function loads configuration based on the ENVIRONMENT variable:
    - local: For local development
    - dev: For development environment
    - stg: For staging environment  
    - prod: For production environment
    
    If ENVIRONMENT is not set, defaults to 'local'.
    """
    environment = os.getenv('ENVIRONMENT', 'local')
    
    # Get the path to the env file relative to this file's location
    # This file is in src/, so env files are in ../config/
    current_dir = Path(__file__).parent  # /path/to/api/src/
    env_file_path = current_dir.parent / 'config' / f'{environment}.env'  # /path/to/api/config/environment.env
    
    if env_file_path.exists():
        print(f"Loading environment config: {env_file_path}")
        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Handle key=value pairs
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Only set if not already set by system environment
                            # This allows system env vars to override file values
                            if key not in os.environ:
                                os.environ[key] = value
                        else:
                            print(f"Warning: Invalid line format in {env_file_path}:{line_num}: {line}")
        except Exception as e:
            print(f"Error loading environment config from {env_file_path}: {e}")
    else:
        print(f"Warning: Environment file not found: {env_file_path}")
    
    print(f"Environment: {environment}")
    return environment


# Note: Call load_environment_config() explicitly from your application
# before importing other modules that depend on environment variables
