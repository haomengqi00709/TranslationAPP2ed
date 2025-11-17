#!/bin/bash

# Start API server with local backend
# This runs translation pipeline locally (requires GPU/CPU resources)

echo "=========================================="
echo "PowerPoint Translation API"
echo "Backend: Local Pipeline"
echo "=========================================="
echo ""

# Set local configuration
export USE_RUNPOD=false

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
