#!/bin/bash
set -e

echo "⏳ Waiting for Ollama to be ready..."
until curl -sf http://ollama:11434/ > /dev/null 2>&1; do
  sleep 2
done
echo "Ollama is ready!"

echo "⏳ Pulling embedding model: qwen3-embedding:0.6b (in background)..."
(
  curl -sf http://ollama:11434/api/pull -d '{"name": "qwen3-embedding:0.6b"}' > /dev/null && \
    echo "Model pulled successfully!" || \
    echo "Failed to pull model!"
) &

echo "🚀 Starting backend server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
