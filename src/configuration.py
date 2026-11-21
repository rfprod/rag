import os

from dotenv import load_dotenv

load_dotenv()

MAX_CONCURRENCY = 1
TIMEOUT = 3

VECTOR_NAME = "rag-app"
RETRIEVER_K = 4

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
QDRANT_API_KEY_READ_ONLY = os.getenv("QDRANT_API_KEY_READ_ONLY", None)
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag-app-py")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_ROUTING_MODEL = os.getenv("OLLAMA_ROUTING_MODEL", "qwen3:1.7b")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:0.6b")
