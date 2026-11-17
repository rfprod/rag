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

2. **Startup script**

The following startup script automatically executed the routines required to run the application.

```bash
# always inspect shell scripts before running them on your machine
bash src/start.sh
```

Successful application startup output would look similar to the example presented below.

```plaintext
[ok] Image 'qdrant/qdrant' already exists locally. Skipping pull.
[i] Starting Qdrant container...
90ac28aca13b86046fa873a71b8491f77d6f16138f11b798778b38ddb4794b9e
67a0ed4988c951b4fb026ca9f2800548f6c7a30c74a9339bd751d2e6de66818e
[i] Qdrant is running with data dir /home/user/qdrant. Waiting for Qdrant...
[i] Qdrant dashboard is available on http://localhost:6333/dashboard
[i] Qdrant status:
67a0ed4988c9   qdrant/qdrant:latest   "./entrypoint.sh"   1 second ago   Up 1 second   0.0.0.0:6333-6334->6333-6334/tcp, [::]:6333-6334->6333-6334/tcp   qdrant-rag-app
[i] Qdrant version check:
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   112  100   112    0     0   117k      0 --:--:-- --:--:-- --:--:--  109k
{"title":"qdrant - vector search engine","version":"1.20.0","commit":"222b2e44ab1c3f17e8246396ead6558e45041df7"}
INFO:     Will watch for changes in these directories: ['/home/user/git/rag/src']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [28317] using StatReload
INFO:     Started server process [28320]
INFO:     Waiting for application startup.
/home/user/git/rag/src/app.py:38: UserWarning: Api key is used with an insecure connection.
  qdrant_client = QdrantClient(
--- startup test ---
Question: What operating systems does nx-ng-starter support?
Answer: I am sorry, but I do not have access to any documents. Therefore, I don't know what operating systems nx-ng-starter supports. I am unable to answer your question based on the provided context.
--- startup test ---
INFO:     Application startup complete.
```

3. **Open in your browser** [http://127.0.0.1:8000/ui](http://127.0.0.1:8000/ui)
