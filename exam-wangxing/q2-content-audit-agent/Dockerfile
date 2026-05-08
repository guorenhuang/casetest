# syntax=docker/dockerfile:1

FROM node:20-alpine AS frontend
WORKDIR /workspace
COPY dataset.json ./dataset.json
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rules.yaml dataset.json ./
COPY src ./src
COPY --from=frontend /workspace/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "q2_audit.main:app", "--host", "0.0.0.0", "--port", "8000"]
