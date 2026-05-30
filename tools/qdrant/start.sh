#!/bin/bash

# Install Qdrant vector database
# https://qdrant.tech/documentation/quick-start/

docker pull qdrant/qdrant

sudo mkdir -p /var/lib/qdrant/storage

if docker ps | grep -q qdrant; then
  echo "Qdrant is already running. Skipping docker run."
else
  echo "Starting Qdrant container..."

  if [ -f .env ]; then
    # shellcheck source=/dev/null
    source .env
  else
    echo "Warning: .env file not found."
  fi

  if [ -z "$QDRANT__SERVICE__API_KEY" ]; then
    echo "Error: QDRANT__SERVICE__API_KEY not found in .env and is not set globally"
    exit 1
  fi

  if [ -z "$QDRANT__SERVICE__READ_ONLY_API_KEY" ]; then
    echo "Error: QDRANT__SERVICE__READ_ONLY_API_KEY not found in .env and is not set globally"
    exit 1
  fi

  # Run Qdrant container
  # This starts Qdrant on port 6333 with persistent storage in /var/lib/qdrant/storage
  # API key authentication documentation: https://github.com/hdt12a1/qdrant-tutorial/blob/main/api_key_authentication.md
  sudo docker run -d \
    --name qdrant \
    --restart always \
    -p 6333:6333 \
    -p 6334:6334 \
    -v /var/lib/qdrant/storage:/qdrant/storage:z \
    -e QDRANT__SERVICE__API_KEY="$QDRANT__SERVICE__API_KEY" \
    -e QDRANT__SERVICE__READ_ONLY_API_KEY="$QDRANT__SERVICE__READ_ONLY_API_KEY" \
    qdrant/qdrant:latest
fi

echo "Qdrant status:"
docker ps | grep qdrant

echo "Qdrant version check:"
curl -H "api-key: $QDRANT__SERVICE__READ_ONLY_API_KEY" http://localhost:6333 | grep version
