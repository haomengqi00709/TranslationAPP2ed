#!/bin/bash

# Start API server with RunPod backend
# This connects your frontend to the RunPod serverless endpoint

echo "=========================================="
echo "PowerPoint Translation API"
echo "Backend: RunPod Serverless"
echo "=========================================="
echo ""

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  Warning: .env file not found!"
    echo "Please create .env file with your API keys"
    echo "See .env.example for template"
    exit 1
fi

# Activate virtual environment
source myenv/bin/activate

# Start the API server
echo "Starting API server on http://localhost:8000"
echo ""
echo "Frontend will be available at: http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 api.py
