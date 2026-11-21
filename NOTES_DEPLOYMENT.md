# Notes: GCP deployment with Terraform

The build log of the deployment, step by step.

The app (FastAPI, PostgreSQL and the React frontend) runs as one Cloud Run service that serves both the API and the React files, with Cloud SQL as the database. Terraform creates every resource.

<br>

## 1. Serve the React build from FastAPI

- [main.py](backend/app/main.py) serves `frontend/dist/` after every API route.
- `app.mount("/assets", StaticFiles(...))` serves the hashed JS and CSS files.
- `serve_frontend` on `/{path:path}`, added last: a file from the root of `dist/` (such as `favicon.svg`), JSON `404` for an unknown `/api` path, `index.html` for any other path.

<br>

## 2. Send the session cookie over HTTPS only

- `secure=True` on `set_cookie` and `delete_cookie` in [mock_session.py](backend/app/mock_session.py).

<br>

## 3. Build the image with a multi-stage Dockerfile

- [Dockerfile](Dockerfile) in the repository root, because the image needs `frontend/` and `backend/`.
- Stage 1, `node:24.14.0-slim`: `npm ci` and `npm run build`; only `dist/` leaves it.
- Stage 2, `python:3.14.10-slim`: `uv sync --locked --no-dev`, then `backend/app` and the build in `/frontend/dist`.
- `CMD` starts `fastapi run` on port `8080`.

<br>

## 4. Keep the build context small with .dockerignore

- [.dockerignore](.dockerignore) is an allow list: `*` ignores everything.
- Let in: `backend/pyproject.toml`, `backend/uv.lock`, `backend/app/`, `frontend/`.
- Kept out: `frontend/node_modules/`, `frontend/dist/`, `**/__pycache__/`, `**/.env*`.

<br>

## 5. Run the image with Compose

- [docker-compose.yaml](docker-compose.yaml) has a second service, `app`, built from the Dockerfile.
- `DATABASE_URL` uses the host `db`, the service name.
- The app is published on `127.0.0.1:8080`.
- A `pg_isready` healthcheck on `db` and `depends_on: condition: service_healthy` make the app wait for the database.
- `db` uses the exact tag `postgres:18.7`.

<br>

## 6. Seed with psql's \copy

- The 12 `COPY` lines in [02-seed.sql](db/init/02-seed.sql) became `\copy`, with the same `/seed/...` paths and options and no `;` at the end.
- psql reads each CSV file and sends the rows over the connection, so the server needs neither the file nor superuser rights.
- The mount comment in [docker-compose.yaml](docker-compose.yaml) names `\copy`.
