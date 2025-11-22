#!/bin/bash

# Smart entrypoint that detects Lambda vs ECS environment
set -e

echo "Landing API starting..."

# Check if we're running in AWS Lambda
if [ -n "$AWS_LAMBDA_RUNTIME_API" ]; then
    echo "Detected Lambda environment - starting Lambda handler"
    # Lambda mode - use the Lambda Runtime Interface Emulator
    exec /lambda-entrypoint.sh lambda_handler.handler
else
    echo "Detected ECS environment - starting web server"
    
    # Change to source directory
    cd /app/api/src
    
    # ECS mode - start the web server with HTTPS
    exec uvicorn app:app \
        --host 0.0.0.0 \
        --port 8000 \
        --ssl-keyfile /app/api/key.pem \
        --ssl-certfile /app/api/cert.pem
fi
