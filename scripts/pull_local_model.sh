#!/bin/sh
# ==============================================================================
# ScamLens Ollama Model Pull Helper
# ==============================================================================
set -e

OLLAMA_HOST="${OLLAMA_BASE_URL:-http://ollama:11434}"
MODEL="${OLLAMA_MODEL:-gemma4:latest}"

echo "Checking Ollama connectivity at ${OLLAMA_HOST}..."
max_attempts=30
attempt=1

until curl -s -f "${OLLAMA_HOST}/api/tags" > /dev/null || [ $attempt -ge $max_attempts ]; do
  echo "Attempt $attempt/$max_attempts: Waiting for Ollama daemon to initialize..."
  sleep 2
  attempt=$((attempt + 1))
done

if [ $attempt -ge $max_attempts ]; then
  echo "Error: Ollama service did not become ready within timeout."
  exit 1
fi

echo "Ollama is ready. Checking if model '${MODEL}' is installed..."
TAGS_OUTPUT=$(curl -s "${OLLAMA_HOST}/api/tags")

if echo "$TAGS_OUTPUT" | grep -q "\"${MODEL}\""; then
  echo "Model '${MODEL}' is already cached in Ollama."
else
  echo "Pulling model '${MODEL}' from Ollama registry (this may take several minutes)..."
  curl -X POST "${OLLAMA_HOST}/api/pull" -d "{\"name\": \"${MODEL}\"}"
  echo "Model '${MODEL}' successfully pulled and ready for offline inference."
fi
