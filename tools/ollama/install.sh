#!/bin/bash

curl -fsSL https://ollama.com/install.sh | sh

ollama --version
ollama pull embeddinggemma
ollama pull gemma3n
ollama list
