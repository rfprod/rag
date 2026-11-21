# RAG application based on Ollama

[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Git](https://img.shields.io/badge/git-2.43.0+-F1502F?logo=git&logoColor=orange)](https://git-scm.com/)

[![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brightgreen.svg)](http://commitizen.github.io/cz-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Requirments

- [Python 3.12](https://www.python.org/downloads/release/python-3120/)
- [Git](https://git-scm.com/)
- [uv](https://github.com/astral-sh/uv)

## Committing changes to the repo

Using [commitizen cli](https://pypi.org/project/commitizen/) is mandatory.


## Quickstart

1. **Virtual environment**

It is recommended to use a virtual environment to work on this project.

The following sequence of commands creates an environment, activates the environment, and installs project dependencies.

```bash
python3 -m venv ~/path-to-venv; \
  source ~/path-to-venv/bin/activate; \
  uv pip compile requirements.txt --output-file requirements.uv.txt; \
  uv pip sync ./requirements.uv.txt
```

2. **Environment variables**

In the project root, create a `.env` file with the following content

```env
QDRANT_URL="http://localhost:6333"
QDRANT_API_KEY="your-secure-read-and-write-key"
QDRANT_API_KEY_READ_ONLY="your-secure-read-only-key"
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="qwen3:4b"
OLLAMA_EMBEDDING_MODEL="qwen3-embedding:4b"
```

3. **Startup script**

The following startup script automatically executed the routines required to run the application.

```bash
# always inspect shell scripts before running them on your machine
bash src/start.sh
```

Successful application startup output would look similar to the example presented below.

```plaintext
[ok] Ollama is already installed, skipping installation.
ollama version is 0.40.16
[ok] Model qwen3-embedding:0.6b already exists locally, skipping.
[ok] Model qwen3:1.7b already exists locally, skipping.
[ok] Model qwen3:4b already exists locally, skipping.
NAME                     ID              SIZE      MODIFIED
qwen3-embedding:0.6b     ac6da0dfba84    639 MB    46 hours ago
qwen3:1.7b               8f68893c685c    1.4 GB    46 hours ago
qwen3:4b                 359d7dd4bcda    2.5 GB    2 days ago
embeddinggemma:latest    85462619ee72    621 MB    2 days ago
gemma3n:latest           0a377808afea    9.8 GB    2 days ago
[ok] Image 'qdrant/qdrant' already exists locally. Skipping pull.
[i] Starting Qdrant container...
384120eb8ea8b1266e842f5e57efab2eedf60172afb8f90ef02965c585aa4a1e
d498bb9e9f03bcfbde6f27d2801acda82043a4f6d82d10781ab3a019df2b4f24
[i] Qdrant is running with data dir /home/user/qdrant. Waiting for Qdrant...
[i] Qdrant dashboard is available on http://localhost:6333/dashboard
[i] EMBEDDINGS=1 set, creating embeddings...
/home/user/py312-venv/lib/python3.12/site-packages/langchain_qdrant/qdrant.py:921: UserWarning: Api key is used with an insecure connection.
  client = QdrantClient(**client_options)
[i] Qdrant status:
d498bb9e9f03   qdrant/qdrant:latest   "./entrypoint.sh"   27 seconds ago   Up 26 seconds   0.0.0.0:6333-6334->6333-6334/tcp, [::]:6333-6334->6333-6334/tcp   qdrant-rag-app
[i] Qdrant version check:
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   112  100   112    0     0   114k      0 --:--:-- --:--:-- --:--:--  109k
{"title":"qdrant - vector search engine","version":"1.20.2","commit":"23065a0bf6857c3e5da45f6c8939cc746cc0580e"}
INFO:     Will watch for changes in these directories: ['/home/user/git/rag/src']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [47088] using StatReload
INFO:     Started server process [47090]
INFO:     Waiting for application startup.
/home/user/git/rag/src/app.py:190: UserWarning: Api key is used with an insecure connection.
  qdrant_client = QdrantClient(
{'rag-app': VectorParams(size=1024, distance=<Distance.COSINE: 'Cosine'>, hnsw_config=None, quantization_config=None, on_disk=None, memory=None, datatype=None, multivector_config=None)}
--- startup test ---
Question: What operating systems does nx-ng-starter support?
Answer: i don't know the specific operating systems that nx-ng-starter supports based on the provided documents. the documents mention it can build web, mobile (with capacitor), and desktop (with electron) applications, but don't explicitly list supported operating systems
--- startup test ---
StreamableHTTP session manager started
INFO:     Application startup complete.
```

3. **Open in your browser** [http://127.0.0.1:8000/ui](http://127.0.0.1:8000/ui)
