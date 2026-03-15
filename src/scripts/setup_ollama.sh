#!/bin/bash
ollama serve &

echo "⏳ Waiting for Ollama server to start..."
# 2. Використовуємо 'ollama list' замість 'curl'
while ! ollama list > /dev/null 2>&1; do
  sleep 2
done

# 3. Качаємо моделі
MODELS=("llama3" "nomic-embed-text")

for model in "${MODELS[@]}"; do
    if ollama list | grep -q "$model"; then
        echo "✅ Model '$model' is already present."
    else
        echo "📥 Pulling model '$model'..."
        ollama pull "$model"
    fi
done

echo "🚀 All models are ready! Keeping the process alive..."

wait