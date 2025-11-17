#!/bin/bash

# Start API server with RunPod backend
# This connects your frontend to the RunPod serverless endpoint

echo "=========================================="
echo "PowerPoint Translation API"
echo "Backend: RunPod Serverless"
echo "=========================================="
echo ""

# Set RunPod configuration
export USE_RUNPOD=true
export RUNPOD_ENDPOINT_ID="io6lj6wjt80mqe"
export RUNPOD_API_KEY="rpa_3O2QGMN26HIIKM3L345AXOB3MH3XWX0N14KZX9TJ13ggys"

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
