FROM ollama/ollama

COPY src/scripts/setup_ollama.sh /setup_ollama.sh
RUN chmod +x /setup_ollama.sh

ENTRYPOINT ["/setup_ollama.sh"]