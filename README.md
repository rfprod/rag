# RAG application based on Ollama

[![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brightgreen.svg)](http://commitizen.github.io/cz-cli/)

## Requirments

In order to run own copy of the project one must fulfill the following requirements.

### Core dependencies

- [Python 3.12](https://www.python.org/downloads/release/python-3120/)
- [Git](https://git-scm.com/)
- [uv](https://github.com/astral-sh/uv)

### Virtual environments

It is recommended to use a virtual environment to work on this project.

The following sequence of commands creates an environment, activates the environment, and installs project dependencies.

```bash
python3 -m venv ~/path-to-venv; \
  source ~/path-to-venv/bin/activate; \
  uv pip compile requirements.txt --output-file requirements.uv.txt; \
  uv pip sync ./requirements.uv.txt
```

## Committing changes to the repo

Using [commitizen cli](https://pypi.org/project/commitizen/) is mandatory.
