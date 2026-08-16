#!/bin/bash

# Install Qdrant vector database
# https://qdrant.tech/documentation/quick-start/

docker pull qdrant/qdrant

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

  if [ -z "$QDRANT_API_KEY" ]; then
    echo "Error: QDRANT_API_KEY not found in .env and is not set globally"
    exit 1
  fi

  if [ -z "$QDRANT_API_KEY_READ_ONLY" ]; then
    echo "Error: QDRANT_API_KEY_READ_ONLY not found in .env and is not set globally"
    exit 1
  fi

  DATA_DIR="$HOME/qdrant"
  mkdir -p "$DATA_DIR"

  # Run Qdrant container
  # This starts Qdrant on port 6333 with persistent storage in /var/lib/qdrant/storage
  # API key authentication documentation: https://github.com/hdt12a1/qdrant-tutorial/blob/main/api_key_authentication.md
  docker run -d \
    --name qdrant-rag-app \
    --restart always \
    -p 6333:6333 \
    -p 6334:6334 \
    -v "$DATA_DIR:/qdrant/storage" \
    -e QDRANT_API_KEY="$QDRANT_API_KEY" \
    -e QDRANT_API_KEY_READ_ONLY="$QDRANT_API_KEY_READ_ONLY" \
    qdrant/qdrant:latest
fi

cleanup() {
  echo -e "${YELLOW}[i]${NC} Qdrant docker container cleanup..."
  docker stop qdrant-rag-app >/dev/null 2>&1 || true
  docker rm qdrant-rag-app >/dev/null 2>&1 || true

  echo -e "${GREEN}[ok]{$NC} Done."
}
trap cleanup EXIT

echo -e "${YELLOW}[i]${NC} Qdrant is running with data dir $DATA_DIR. Waiting for Qdrant..."

MAX_WAIT_SEC=60
SLEEP_SEC=1
ELAPSED=0
STARTUP_STATUS=""

while [ "$ELAPSED" -lt "$MAX_WAIT_SEC" ]; do
  STARTUP_STATUS="$(curl -s -o /dev/null -w "%{http_code}" -H "api-key: $QDRANT_API_KEY" http://localhost:6333/collections || echo "curl_error")"
  if [ "$STARTUP_STATUS" = "200" ]; then
    break
  fi
  sleep "$SLEEP_SEC"
  ELAPSED=$((ELAPSED + SLEEP_SEC))
done
if [ "$STARTUP_STATUS" != "200" ]; then
  echo -e "${RED}[err]{$NC} Qdrant startup timeout. Last HTTP status: $STARTUP_STATUS"
  echo -e "${YELLOW}[i]${NC} Qdrant container logs:"
  docker logs --tail 50 qdrant-rag-app || echo -e "${RED}[warn]${NC} Could not fetch qdrant-rag-app Docker logs."
  exit 1
fi

echo "Qdrant status:"
docker ps | grep qdrant

echo "Qdrant version check:"
curl -H "api-key: $QDRANT_API_KEY_READ_ONLY" http://localhost:6333 | grep version

cd "$(dirname "$0")" || exit 1

uvicorn api:app --reload
