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

##
# Reports usage.
##
print_help() {
  print_info_title "<< ${0} usage >>"
  print_usage_tip "bash tools/shell/run.sh ?" "print help"
  print_usage_tip "bash tools/shell/push.sh APPLICATION_NAME_WITH_ENVIRONMENT" "push docker image to the repository"
  print_gap

  print_info_message "Supported application names"
  print_gap

  for IMAGE_KEY in "${!IMAGES[@]}"; do
    print_value "${IMAGE_KEY}"
  done
}

##
# Image support checker.
##
check_image_support() {
  print_info_title "<< Checking Docker image support >>"
  print_name_and_value "name" "$1"
  print_gap

  local KEY
  KEY="$1"

  if [ -z "${IMAGES[$KEY]}" ]; then
    print_error_title "Image is not supported"
    print_name_and_value "image key" "$KEY"
    print_gap

    exit 1
  else
    print_success_title "Image is supported, proceeding"
    print_gap
  fi
}

##
# Pushes docker container.
##
push_docker_container() {
  local IMAGE_KEY
  IMAGE_KEY="$1"

  check_image_support "$IMAGE_KEY"

  local IMAGE
  IMAGE=${IMAGES[$IMAGE_KEY]}

  docker push "$IMAGE"
}

##
# Docker registry push control flow.
##
if [ 1 -gt $# ]; then
  print_help
  exit 1
elif [ "$1" == "?" ]; then
  print_help
else
  push_docker_container "$1"
fi
