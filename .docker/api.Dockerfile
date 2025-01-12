FROM ollama/ollama:0.5.5

# TODO: this container configuration is not complete

# Create app directory.
WORKDIR /app

COPY /src ./src
COPY /requirements.txt ./

RUN apt install python3.12; \
  python3 --version; \
  pip3 install -r ./requirements.txt; \
  ollama --version; \
  ollama pull llama3.2; \
  ollama list

# Configure exposed port.
EXPOSE 8000
# Set up a health check.
HEALTHCHECK --interval=5m --timeout=3s CMD curl --fail http://localhost:8000 || exit 1
# Define startup command.
CMD [ "python3", "./src/api.py" ]
