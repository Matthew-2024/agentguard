FROM python:3.12-slim AS backend

WORKDIR /app
ENV PYTHONPATH=/app

COPY backend/requirements.txt /app/agentguard/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/agentguard/backend/requirements.txt

COPY . /app/agentguard
RUN adduser --disabled-password --gecos "" agentguard \
    && mkdir -p /data \
    && chown -R agentguard:agentguard /app /data

USER agentguard

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "agentguard.backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
