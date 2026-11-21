#!/bin/bash

set -e

if command -v ollama >/dev/null 2>&1; then
  echo "Ollama is already installed, skipping installation."
else
  echo "Ollama not found. Installing..."
  curl -fsSL https://ollama.com/install.sh | sh
fi

ollama --version

declare MODELS=("qwen3-embedding:0.6b" "qwen3:1.7b" "qwen3:4b")

INSTALLED_MODELS=$(ollama list | awk 'NR>1 {print $1}')

for MODEL in "${MODELS[@]}"; do
  if grep -Fxq "$MODEL" <<< "$INSTALLED_MODELS"; then
    echo "Model $MODEL already exists locally, skipping."
  else
    echo "Pulling model $MODEL..."
    ollama pull "$MODEL"
  fi
done

ollama list
