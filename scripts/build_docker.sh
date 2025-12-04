#!/bin/bash
set -e

echo "Building Portfolio Prism Docker image..."

# Load secrets
if [ -f .env.docker ]; then
    source .env.docker
else
    echo "Missing .env.docker - copy from .env.docker.example"
    exit 1
fi

# Validate secrets
if [ -z "$FINNHUB_API_KEY" ]; then
    echo "FINNHUB_API_KEY not set"
    exit 1
fi

if [ -z "$GITHUB_ISSUES_TOKEN" ]; then
    echo "GITHUB_ISSUES_TOKEN not set"
    exit 1
fi

# Build
docker build \
    --build-arg FINNHUB_API_KEY="$FINNHUB_API_KEY" \
    --build-arg GITHUB_ISSUES_TOKEN="$GITHUB_ISSUES_TOKEN" \
    -t portfolio-prism:latest \
    -t ghcr.io/skeptomenos/portfolio-prism:latest \
    .

echo "Build complete!"
echo ""
echo "To run locally:"
echo "  docker run -p 8501:8501 portfolio-prism:latest"
echo ""
echo "To push to GitHub Container Registry:"
echo "  echo \$GITHUB_TOKEN | docker login ghcr.io -u skeptomenos --password-stdin"
echo "  docker push ghcr.io/skeptomenos/portfolio-prism:latest"
