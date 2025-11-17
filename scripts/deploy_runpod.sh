#!/bin/bash

# RunPod Serverless Deployment Script
# This script builds and pushes the Docker image to Docker Hub

set -e  # Exit on error

echo "=================================="
echo "RunPod Serverless Deployment"
echo "=================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Get Docker Hub username
read -p "Enter your Docker Hub username: " DOCKER_USERNAME

# Get image name
read -p "Enter image name (default: pptx-translator): " IMAGE_NAME
IMAGE_NAME=${IMAGE_NAME:-pptx-translator}

# Get version tag
read -p "Enter version tag (default: latest): " VERSION_TAG
VERSION_TAG=${VERSION_TAG:-latest}

# Full image name
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION_TAG}"

echo ""
echo "📦 Building Docker image: ${FULL_IMAGE_NAME}"
echo ""
echo "Note: This will clone fast_align from GitHub during build"
echo "      (Alternatively, you can build from parent dir to use local copy)"
echo ""

# Build the Docker image (run from project root)
cd "$(dirname "$0")/.."  # Go to project root
docker build \
    -f scripts/Dockerfile.runpod \
    -t ${FULL_IMAGE_NAME} \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --progress=plain \
    .

echo ""
echo "✅ Build complete!"
echo ""

# Ask if user wants to push
read -p "Push to Docker Hub? (y/n): " PUSH_CONFIRM

if [[ "$PUSH_CONFIRM" == "y" || "$PUSH_CONFIRM" == "Y" ]]; then
    echo ""
    echo "🔐 Logging into Docker Hub..."
    docker login

    echo ""
    echo "📤 Pushing image to Docker Hub..."
    docker push ${FULL_IMAGE_NAME}

    echo ""
    echo "✅ Image pushed successfully!"
    echo ""
    echo "=================================="
    echo "Next Steps:"
    echo "=================================="
    echo ""
    echo "1. Go to https://www.runpod.io/console/serverless"
    echo "2. Click '+ New Endpoint'"
    echo "3. Use this image: ${FULL_IMAGE_NAME}"
    echo "4. Select GPU: RTX 4090 (recommended)"
    echo "5. Set Container Disk: 20 GB"
    echo "6. Set Min Workers: 0, Max Workers: 3"
    echo "7. Enable FlashBoot"
    echo "8. Deploy!"
    echo ""
    echo "See docs/RUNPOD_DEPLOYMENT.md for detailed instructions"
    echo ""
else
    echo ""
    echo "ℹ️  Build complete but not pushed."
    echo "To push later, run: docker push ${FULL_IMAGE_NAME}"
    echo ""
fi
