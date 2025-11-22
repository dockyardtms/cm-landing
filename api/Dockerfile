# Landing API multi-stage Dockerfile (legacy, optional for local use)
# Supports both ECS-style and Lambda-style containers from a single file

# ============================================================================
# SHARED BASE STAGE - Common application setup
# ============================================================================
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy API source code
COPY api/src/ ./api/src/
COPY api/env/ ./api/env/
COPY api/requirements.txt ./api/

# Generate self-signed SSL certificate for HTTPS (in api directory)
WORKDIR /app/api
RUN openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
    -subj "/C=US/ST=CA/L=San Francisco/O=Credomax/OU=LandingAPI/CN=localhost"

# ============================================================================
# ECS TARGET - For ECS/Fargate deployment
# ============================================================================
FROM base AS ecs

# Build argument for version (passed at build time)
ARG VERSION=0.1.0

# Set the VERSION environment variable
ENV VERSION=${VERSION}

# Install Python dependencies from api directory
WORKDIR /app/api
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Set environment variables for proper imports
ENV PYTHONPATH=/app/api/src

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f -k https://localhost:8000/health || exit 1

# Set working directory to api/src for proper imports
WORKDIR /app/api/src

# Start the FastAPI server directly
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "../key.pem", "--ssl-certfile", "../cert.pem"]

# ============================================================================
# LAMBDA TARGET - For AWS Lambda deployment
# ============================================================================
FROM public.ecr.aws/lambda/python:3.12 AS lambda

# Re-declare the build argument for this stage
ARG VERSION=0.1.0

# Set the VERSION environment variable
ENV VERSION=${VERSION}

# Copy the entire application from the base stage
COPY --from=base /app /var/task

# Install Python dependencies from api directory
WORKDIR /var/task/api
RUN pip install --no-cache-dir -r requirements.txt

# Set working directory to where the lambda_handler is located
WORKDIR /var/task/api/src

# Set environment variables - ensure proper Python path
ENV PYTHONPATH=/var/task/api/src:/var/task

# Set the Lambda entrypoint - run from the directory containing lambda_handler.py
ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["lambda_handler.handler"]
