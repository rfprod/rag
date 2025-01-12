#!/bin/bash

curl -fsSL https://ollama.com/install.sh | sh

ollama --version
ollama pull llama3.2
ollama list
