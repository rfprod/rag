#!/bin/bash

declare -a CODEOWNERS=()

while read -r LINE; do
  if [ "$DEBUG" = "true" ]; then
    echo "[DEBUG] read: $LINE"
  fi

  case "$LINE" in
  *@*)
    NAME=$(echo "$LINE" | sed -r 's/^.*@//g')
    if [ "$DEBUG" = "true" ]; then
      echo "[DEBUG] name: $NAME"
    fi

    case "${CODEOWNERS[@]}" in *"\"$NAME\""*)
      if [ "$DEBUG" = "true" ]; then
        echo "[DEBUG] duplicated $NAME"
      fi
      ;;
    *)
      CODEOWNERS+=("\"$NAME\"")
      ;;
    esac
    ;;
  esac
done <.github/CODEOWNERS

if [ "$DEBUG" = "true" ]; then
  printf "[DEBUG] codeowners %s" "${CODEOWNERS[@]}"
fi

OUTPUT="["

for ITEM in "${CODEOWNERS[@]}"; do
  if [ "$DEBUG" = "true" ]; then
    echo "[DEBUG] i: $ITEM"
  fi
  OUTPUT+="$ITEM"
  OUTPUT+=","
done

OUTPUT=${OUTPUT::-1}

OUTPUT+="]"

echo "$OUTPUT"
