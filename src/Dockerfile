FROM python:3.12-bookworm
WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH=/app/src
COPY .  .
COPY src/scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x src/scripts/entrypoint.sh


ENTRYPOINT ["/bin/bash", "/app/src/scripts/entrypoint.sh"]