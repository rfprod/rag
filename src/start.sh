#!/bin/bash
set -euo pipefail

# Install Qdrant vector database
# https://qdrant.tech/documentation/quick-start/

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
NC_BOLD='\033[1m'

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo -e "${RED}[err]${NC} activate a ${NC_BOLD}Python virtual environment${NC} before running this script." >&2
  exit 1
fi

print_help() {
  local SCRIPT_NAME
  SCRIPT_NAME="$(basename "$0")"

  echo -e "${NC_BOLD}NAME${NC} \n\
    ${SCRIPT_NAME} - Start a local Qdrant vector database in Docker and run the API. \n"

  echo -e "${NC_BOLD}SYNOPSIS${NC} \n\
    ./${SCRIPT_NAME} [${YELLOW}-h${NC} | ${YELLOW}--help${NC}] \n\
    [${YELLOW}QDRANT_IMAGE${NC}=<image>] [${YELLOW}FORCE_PULL_QDRANT${NC}=0|1] [${YELLOW}CREATE_EMBEDDINGS${NC}=0|1] \n\
    [${YELLOW}QDRANT_API_KEY${NC}=<key>] [${YELLOW}QDRANT_API_KEY_READ_ONLY${NC}=<key>] ./${SCRIPT_NAME} \n"

  echo -e "${NC_BOLD}DESCRIPTION${NC} \n\
    This script prepares and runs a Qdrant container named 'qdrant-rag-app' \n\
    with persistent storage in ${YELLOW}\$HOME${NC}/qdrant. It then optionally generates \n\
    embeddings with src/embeddings.py, waits until Qdrant responds, and \n\
    starts the API with 'uvicorn api:app --reload'. \n\
    \n\
    When the script exits, the Qdrant container is stopped and removed, \n\
    and the 'app-rag-net' Docker network is removed. \n\
    \n\
    Qdrant is available at: \n\
      REST API:   http://localhost:6333 \n\
      gRPC:       localhost:6334 \n\
      Dashboard:  http://localhost:6333/dashboard \n"

  echo -e "${NC_BOLD}OPTIONS${NC} \n\
    ${YELLOW}-h${NC}, ${YELLOW}--help${NC} \n\
        Show this help message and exit. \n"

  echo -e "${NC_BOLD}ENVIRONMENT VARIABLES${NC} \n\
    ${YELLOW}QDRANT_API_KEY${NC} (required if not in .env) \n\
        Admin API key passed to the Qdrant container. Also used for the \n\
        startup health check. \n\
    \n\
    ${YELLOW}QDRANT_API_KEY_READ_ONLY${NC} (required if not in .env) \n\
        Read-only API key passed to the Qdrant container. Used for the \n\
        version check. \n\
    \n\
    ${YELLOW}QDRANT_IMAGE${NC} (default: qdrant/qdrant) \n\
        Docker image to use for Qdrant. \n\
    \n\
    ${YELLOW}FORCE_PULL_QDRANT${NC} (default: 0) \n\
        Set to 1 to pull the Qdrant image even if it already exists locally. \n\
    \n\
    ${YELLOW}CREATE_EMBEDDINGS${NC} (default: 1) \n\
        Set to 1 to run python3 ./src/embeddings.py before starting the API. \n\
        Set to 0 to skip this step. \n"

  echo -e "${NC_BOLD}FILES${NC} \n\
    .env \n\
        Optional file in the current directory, sourced to load the API keys. \n\
        Example contents: \n\
          ${YELLOW}QDRANT_API_KEY${NC}=your-admin-key \n\
          ${YELLOW}QDRANT_API_KEY_READ_ONLY${NC}=your-read-only-key \n\
    \n\
    src/embeddings.py \n\
        Embedding script, required when CREATE_EMBEDDINGS=1. \n\
    \n\
    api.py \n\
        FastAPI application, served by uvicorn as 'api:app'. \n"

  echo -e "${NC_BOLD}PREREQUISITES${NC} \n\
    - Docker installed and the daemon running \n\
    - Python 3 (if CREATE_EMBEDDINGS=1) \n\
    - curl \n\
    - uvicorn installed (for the API) \n\
    - Ports 6333 and 6334 free on the host \n"

  echo -e "${NC_BOLD}EXAMPLES${NC} \n\
    Start Qdrant and the API with default settings: \n\
        ./${SCRIPT_NAME} \n\
    Skip embedding creation: \n\
        ${YELLOW}CREATE_EMBEDDINGS${NC}=0 ./${SCRIPT_NAME} \n\
    Use a specific image tag and force a fresh pull: \n\
        ${YELLOW}QDRANT_IMAGE${NC}=qdrant/qdrant:v1.12.0 ${YELLOW}FORCE_PULL_QDRANT${NC}=1 ./${SCRIPT_NAME} \n\
    Pass API keys directly instead of using .env: \n\
        ${YELLOW}QDRANT_API_KEY${NC}=abc ${YELLOW}QDRANT_API_KEY_READ_ONLY${NC}=def ./${SCRIPT_NAME} \n\
    Show this help: \n\
        ./${SCRIPT_NAME} ${YELLOW}--help${NC} \n"

  echo -e "${NC_BOLD}EXIT STATUS${NC} \n\
    0 on success, 1 on error (for example, Docker is unavailable, API keys \n\
    are missing, or Qdrant does not start within 60 seconds). \n"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  print_help
  exit 0
fi

prepare_ollama() {
  if command -v ollama >/dev/null 2>&1; then
    echo -e "${GREEN}[ok]${NC} ${NC_BOLD}Ollama${NC} is already installed, skipping installation."
  else
    echo -e "${YELLOW}[i]${NC} ${NC_BOLD}Ollama${NC} not found. Installing..."
    curl -fsSL https://ollama.com/install.sh | sh
  fi

  ollama --version

  declare MODELS=("qwen3-embedding:0.6b" "qwen3:1.7b" "qwen3:4b")

  INSTALLED_MODELS=$(ollama list | awk 'NR>1 {print $1}')

  for MODEL in "${MODELS[@]}"; do
    if grep -Fxq "$MODEL" <<< "$INSTALLED_MODELS"; then
      echo -e "${GREEN}[ok]${NC} Model ${NC_BOLD}$MODEL${NC} already exists locally, skipping."
    else
      echo -e "${YELLOW}[i]${NC} Pulling model ${NC_BOLD}$MODEL${NC}..."
      ollama pull "$MODEL"
    fi
  done

  ollama list
}

prepare_ollama

prepare_qdrant_image() {
  local IMAGE
  IMAGE="${QDRANT_IMAGE:-qdrant/qdrant}"

  local FORCE_PULL
  FORCE_PULL="${FORCE_PULL_QDRANT:-0}"

  if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}[err]${NC} docker is not installed or not on ${NC_BOLD}PATH${NC}." >&2
    exit 1
  fi

  if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}[err]${NC} cannot reach the ${NC_BOLD}Docker${NC} daemon. Is it running?" >&2
    exit 1
  fi

  if [[ "$FORCE_PULL" == "1" ]]; then
    echo -e "${YELLOW}[i]${NC} ${NC_BOLD}FORCE_PULL=1${NC} set, pulling '$IMAGE'..."
    docker pull "$IMAGE"
  elif docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo -e "${GREEN}[ok]${NC} Image '$IMAGE' already exists locally. Skipping pull."
  else
    echo -e "${YELLOW}[i]${NC} Image '$IMAGE' not found locally. Pulling..."
    docker pull "$IMAGE"
  fi
}

prepare_qdrant_image

run_qdrant() {
  if docker ps | grep -q qdrant; then
    echo -e "${GREEN}[ok]${NC} ${NC_BOLD}Qdrant${NC} is already running. Skipping docker run."
  else
    echo -e "${YELLOW}[i]${NC} Starting ${NC_BOLD}Qdrant${NC} container..."

    if [ -f .env ]; then
      # shellcheck source=/dev/null
      source .env
    else
      echo -e "${YELLOW}[warn]${NC} ${NC_BOLD}.env${NC} file not found."
    fi

    if [ -z "${QDRANT_API_KEY:-}" ]; then
      echo -e "${RED}[err]${NC} ${NC_BOLD}QDRANT_API_KEY${NC} not found in .env and is not set globally."
      exit 1
    fi

    if [ -z "${QDRANT_API_KEY_READ_ONLY:-}" ]; then
      echo -e "${RED}[err]${NC} ${NC_BOLD}QDRANT_API_KEY_READ_ONLY${NC} not found in .env and is not set globally."
      exit 1
    fi

    local DATA_DIR
    DATA_DIR="$HOME/qdrant"
    mkdir -p "$DATA_DIR"

    # Run Qdrant container
    # This starts Qdrant on port 6333 with persistent storage in /var/lib/qdrant/storage
    # API key authentication documentation: https://github.com/hdt12a1/qdrant-tutorial/blob/main/api_key_authentication.md
    docker network create app-rag-net
    docker run -d \
      --name qdrant-rag-app \
      --restart always \
      --network app-rag-net \
      -p 6333:6333 \
      -p 6334:6334 \
      -v "$DATA_DIR:/qdrant/storage" \
      -e QDRANT_API_KEY="$QDRANT_API_KEY" \
      -e QDRANT_API_KEY_READ_ONLY="$QDRANT_API_KEY_READ_ONLY" \
      qdrant/qdrant:latest

    echo -e "${YELLOW}[i]${NC} ${NC_BOLD}Qdrant${NC} is running with data dir $DATA_DIR. Waiting for Qdrant..."

    echo -e "${YELLOW}[i]${NC} ${NC_BOLD}Qdrant${NC} dashboard is available on ${NC_BOLD}http://localhost:6333/dashboard${NC}"
  fi
}

run_qdrant

create_embeddings() {
  local EMBEDDINGS
  EMBEDDINGS="${CREATE_EMBEDDINGS:-1}"

  if [[ "$EMBEDDINGS" == "1" ]]; then
    echo -e "${YELLOW}[i]${NC} ${NC_BOLD}EMBEDDINGS=1${NC} set, creating embeddings..."
    python3 ./src/embeddings.py
  fi
}

create_embeddings

cleanup() {
  echo -e "${YELLOW}[i]${NC} ${NC_BOLD}Qdrant${NC} docker container cleanup..."
  docker stop qdrant-rag-app >/dev/null 2>&1 || true
  docker rm qdrant-rag-app >/dev/null 2>&1 || true
  docker network rm app-rag-net

  echo -e "${GREEN}[ok]{$NC} Done."
}
trap cleanup EXIT

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
  echo -e "${RED}[err]${NC} ${NC_BOLD}Qdrant${NC} startup timeout. Last HTTP status: $STARTUP_STATUS"
  echo -e "${YELLOW}[i]${NC} ${NC_BOLD}Qdrant${NC} container logs:"
  docker logs --tail 50 qdrant-rag-app || echo -e "${RED}[warn]${NC} Could not fetch ${NC_BOLD}qdrant-rag-app${NC} Docker container logs."
  exit 1
fi

echo -e "${YELLOW}[i]${NC} ${NC_BOLD}Qdrant${NC} status:"
docker ps | grep qdrant

echo -e "${YELLOW}[i]${NC} ${NC_BOLD}Qdrant${NC} version check:"
curl -H "api-key: $QDRANT_API_KEY_READ_ONLY" http://localhost:6333 | grep version

cd "$(dirname "$0")" || exit 1

uvicorn api:app --reload
