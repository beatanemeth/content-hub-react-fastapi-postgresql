# Stage 1: build the React app; only dist/ leaves this stage
FROM node:24.14.0-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: the image Cloud Run runs
FROM python:3.14.10-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/
WORKDIR /app
# The lock files come before the code, so a code change reuses the installed packages
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev
COPY backend/app ./app
# main.py is /app/app/main.py and looks for the build two folders up: /frontend/dist
COPY --from=frontend /frontend/dist /frontend/dist
# Cloud Run sends requests to port 8080 by default; fastapi run listens on 0.0.0.0
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "8080"]
