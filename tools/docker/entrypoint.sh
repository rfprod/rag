#!/bin/sh

set -eu

ollama serve &
OLLAMA_PID=$!

cleanup() {
    kill "$OLLAMA_PID" 2>/dev/null || true
    wait "$OLLAMA_PID" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

ATTEMPT=0
until ollama list >/dev/null 2>&1; do
    if ! kill -0 "$OLLAMA_PID" 2>/dev/null; then
        echo "Ollama server exited before becoming ready" >&2
        exit 1
    fi

    ATTEMPT=$((ATTEMPT + 1))
    if [ "$ATTEMPT" -ge 60 ]; then
        echo "Ollama server did not start" >&2
        exit 1
    fi
    sleep 1
done

ollama pull embeddinggemma
ollama pull gemma3n
ollama list
python /app/src/api.py
