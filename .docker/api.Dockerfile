FROM ollama/ollama:0.40.3

##
# This container image needs three environment variables provided at runtime to operate:
# - QDRANT_URL
# - QDRANT_API_KEY
# - QDRANT_API_KEY_READ_ONLY
##

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY /src ./src
COPY /src/static ./static
COPY /requirements.txt ./
COPY /tools/docker/entrypoint.sh ./
RUN chmod +x ./entrypoint.sh

RUN apt-get update \
    && apt-get install -y --no-install-recommends software-properties-common gnupg dirmngr ca-certificates \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3.12 python3.12-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3.12 --version \
    && python3.12 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN python -m pip install --no-cache-dir -r ./requirements.txt \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
HEALTHCHECK --interval=5m --timeout=3s CMD curl --fail http://localhost:8000 || exit 1
ENTRYPOINT []
CMD ["/app/entrypoint.sh"]
