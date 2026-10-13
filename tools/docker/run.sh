#!/bin/bash

source tools/utils/print-utils.sh ''

source tools/utils/config.sh

##
# Container registry base path.
##
CONTAINER_REGISTRY=rfprod/rag

##
# Supported images.
# Associative array mapping: <app name | docker file name> - <docker image name>
##
declare -A IMAGES=(
  ["api-development"]="$CONTAINER_REGISTRY"":api-development-latest"
  ["api-production"]="$CONTAINER_REGISTRY"":api-production-latest"
)

declare -A PORT_MAPPING=(
  ["default"]="8080:8080"
)

##
# Reports usage.
##
print_help() {
  print_info_title "<< ${0} usage >>"
  print_usage_tip "bash tools/shell/run.sh ?" "print help"
  print_usage_tip "bash tools/shell/run.sh APPLICATION" "run APPLICATION docker container"
  print_usage_tip "bash tools/shell/run.sh APPLICATION debug" "run APPLICATION docker container in debug mode"
  print_gap

  print_info_message "Supported applications"
  print_gap

  for SUPPORTED_IMAGE_KEY in "${!IMAGES[@]}"; do
    print_value "${SUPPORTED_IMAGE_KEY}"
  done
  print_gap
}

##
# Runs a container image.
##
run_container() {
  print_info_title "<< Run Docker container image: $1 >>"
  print_gap

  local APP_NAME
  APP_NAME=$1

  local IMAGE_NAME
  IMAGE_NAME=${IMAGES[$APP_NAME]}

  local PORTS_MAP
  PORTS_MAP=${PORT_MAPPING[$APP_NAME]:-"8080:8080"}

  if [ -z "$IMAGE_NAME" ]; then
    print_error_title "Application is not supported"
    print_name_and_value "application key" "$APP_NAME"
    print_gap

    print_help
    exit 1
  fi

  print_success_title "Application $APP_NAME is supported, proceeding"
  print_gap

  echo "$IMAGE_NAME"

  if [ "$2" = "debug" ]; then
    docker run --rm --network app-rag-net -e QDRANT_URL="${QDRANT_URL}" -e QDRANT_API_KEY="${QDRANT_API_KEY}" -e QDRANT_API_KEY_READ_ONLY="${QDRANT_API_KEY_READ_ONLY}" --name "$APP_NAME" -it -p 127.0.0.1:"$PORTS_MAP" "$IMAGE_NAME" /bin/sh
  else
    docker run --rm --network app-rag-net -e QDRANT_URL="${QDRANT_URL}" -e QDRANT_API_KEY="${QDRANT_API_KEY}" -e QDRANT_API_KEY_READ_ONLY="${QDRANT_API_KEY_READ_ONLY}" --name "$APP_NAME" -it -p 127.0.0.1:"$PORTS_MAP" "$IMAGE_NAME"
  fi
}

if [ "$1" = "?" ]; then
  print_help
elif [ 1 -gt $# ]; then
  print_help
  exit 1
else
  run_container "$1" "$2"
fi
