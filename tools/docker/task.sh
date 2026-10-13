#!/bin/bash

source tools/utils/print-utils.sh ''

source tools/utils/config.sh

##
# Reports usage error.
##
print_help() {
  print_info_title "<< ${0} usage >>"
  print_usage_tip "bash tools/shell/task.sh cleanup" "utility task, removes stopped containers and cleans up untagged images (should be used on runners which use CI container images)"
  print_usage_tip "bash tools/shell/task.sh login USERNAME PASSWORD" "docker login, requires a user name and a password"
  print_gap

  exit 1
}

docker_login() {
  local DOCKER_REGISTRY_USER
  DOCKER_REGISTRY_USER="$1"
  local DOCKER_REGISTRY_PASS
  DOCKER_REGISTRY_PASS="$2"

  echo "${DOCKER_REGISTRY_PASS}" | docker login -u "$DOCKER_REGISTRY_USER" "$LOGIN_URL" --password-stdin
}

if [ 1 -gt $# ]; then
  print_help
elif [ "$1" = "cleanup" ]; then
  ##
  # Removes stopped containers and cleans up untagged images.
  ##
  print_info_title "Cleaning up container images"
  print_gap

  EXIT_CODE=0
  DOCKER_EXISTS=$(command -v docker) || EXIT_CODE=1

  print_name_and_value "docker exists" "$DOCKER_EXISTS"
  print_name_and_value "docker checker exit code" "$EXIT_CODE"
  print_gap

  if [ "$EXIT_CODE" -eq 0 ]; then
    print_info_message "cleaning up docker: removing all stopped containers"
    print_gap
    docker rm -v -f "$(docker ps -qa)" || true

    print_info_message "cleaning up docker: removing all untagged images"
    print_gap
    docker rmi "$(docker images | grep "^<none>" | awk "{print $3}")" || true

    print_info_message "cleaning up docker: removing unused images"
    print_gap
    docker image prune -af
  else
    print_info_message "docker is not installed, nothing to clean up"
    print_gap
  fi
elif [ "$1" = "login" ]; then
  docker_login "$2" "$3"
else
  print_help
fi
