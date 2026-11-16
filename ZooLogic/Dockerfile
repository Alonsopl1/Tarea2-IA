# Un único entorno para Python + intérprete SWI-Prolog.
# La segunda opción usa Ollama en otro contenedor (compose.yaml).
FROM python:3.12-slim-bookworm
RUN apt-get update \
    && apt-get install -y --no-install-recommends swi-prolog-nox \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
ENV PYTHONUNBUFFERED=1 \
    ZOOLOGIC_HOST=0.0.0.0 \
    PORT=8765 \
    OLLAMA_URL=http://ollama:11434 \
    OLLAMA_MODEL=llama3.2:3b
EXPOSE 8765
CMD ["python", "servidor.py"]
