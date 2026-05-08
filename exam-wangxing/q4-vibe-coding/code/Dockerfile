# syntax=docker/dockerfile:1

FROM node:20-alpine AS frontend
WORKDIR /workspace/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1
ENV STORYBOARD_DB_PATH=/app/data/storyboard.db
ENV STATIC_DIR=/app/static

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY backend/ ./
RUN mkdir -p /app/data

COPY --from=frontend /workspace/frontend/dist /app/static

EXPOSE 8000
VOLUME ["/app/data"]

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
