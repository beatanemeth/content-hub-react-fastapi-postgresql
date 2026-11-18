# Notes: GCP deployment with Terraform

This file is the build log of the deployment: the commands, files and checks, in the order the deployment was built. The plan and its reasons are in [evolution_roadmap_deployment.md](docs/claude/evolution_roadmap_deployment.md). The build log of the local app is [NOTES.md](NOTES.md).

<br>

## Contents

- [Goal](#goal)
- **Build log steps in development order:**
  1. [Serve the React build from FastAPI](#1-serve-the-react-build-from-fastapi)
  2. [Build the image with a multi-stage Dockerfile](#2-build-the-image-with-a-multi-stage-dockerfile)
  3. [Keep the build context small with .dockerignore](#3-keep-the-build-context-small-with-dockerignore)
  4. [Run the image with Compose](#4-run-the-image-with-compose)

<br>

## Goal

The app at tag `v0.3.0` (FastAPI, PostgreSQL and the React frontend) runs on GCP. One Cloud Run service serves the API and the React files, and Cloud SQL holds the database. Terraform creates every resource. The API contract does not change.

**One container for the frontend and the backend:**

- **The built frontend is only files:** `npm run build` writes `index.html`, a JS file and a CSS file to `dist/`. No Node.js server runs in production, so FastAPI can serve these files.
- **One origin:** the page and the API share one address. The session cookie works unchanged, the API needs no CORS, and the frontend keeps its relative `/api/...` URLs.
- **Enough for this demo:** separate containers (for example, nginx for the React files) pay off when the frontend and the backend scale or are released separately. Here they would only add a second Cloud Run service, CORS and a cross-site cookie.

<br>

## 1. Serve the React build from FastAPI

- **Before:** two servers ran on the laptop. Vite served the React app on port 5173 and forwarded `/api` to FastAPI on port 8000. FastAPI served only the API.
- **Why the change:** Cloud Run runs one container, and the app needs no second server. When FastAPI also serves the built React files, the browser still sees one origin, as with the Vite proxy. So the API needs no CORS, and the session cookie keeps working unchanged.

Branch `chore/docker-image`. [main.py](backend/app/main.py) serves the files in `frontend/dist/` after every API route:

| Part                                     | Does                                                                                                                                        |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `FRONTEND_DIST`                          | The build folder, found from the location of `main.py`                                                                                      |
| `app.mount("/assets", StaticFiles(...))` | Serves the JS and CSS files that Vite names with a content hash                                                                             |
| `serve_frontend` on `/{path:path}`       | Returns a file from the root of `dist/` (such as `favicon.svg`), JSON `404` for an unknown `/api` path, and `index.html` for any other path |

Build the frontend in `frontend/`, then start the server in `backend/` (the database container must be running):

```bash
npm run build
```

```bash
uv run fastapi dev app/main.py
```

**Expected result:**

`serve_frontend` answers every path that no other route answers. FastAPI checks the routes in the order they are added, so `serve_frontend` is added last.

| Check                                                | Result                              | Shows                                                                                          |
| ---------------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------- |
| Reload `http://localhost:8000/blog/1` in the browser | The post, not a `404`               | `/blog/1` is a React page, not a file. FastAPI returns `index.html`, and React shows the post. |
| `curl -i http://localhost:8000/api/unknown`          | `404` with `{"detail":"Not Found"}` | A wrong API path still gets a JSON error, not the React page.                                  |
| `curl -i http://localhost:8000/api/tags`             | `200` with the tags                 | `serve_frontend` does not hide the API routes.                                                 |
| `http://localhost:8000/docs` in the browser          | The Swagger UI                      | `serve_frontend` does not hide FastAPI's own pages either.                                     |

<br>

## 2. Build the image with a multi-stage Dockerfile

- **Before:** the app ran from the source folders, with Node.js and uv installed on the laptop.
- **Why the change:** Cloud Run runs a container image. The image needs the backend, its packages and the built React files, but not Node.js.

[Dockerfile](Dockerfile), in the repository root because the image needs both `frontend/` and `backend/`:

| Stage                    | Does                                                                                                           |
| ------------------------ | -------------------------------------------------------------------------------------------------------------- |
| 1: `node:24.14.0-slim`   | Runs `npm ci` and `npm run build`; only `dist/` leaves this stage                                              |
| 2: `python:3.14.10-slim` | Installs the packages with `uv sync --locked --no-dev`, copies `backend/app` and the build to `/frontend/dist` |
| `CMD`                    | Starts `fastapi run` on port `8080`, the port Cloud Run sends requests to                                      |

- **Exact tags:** the Node.js, Python and uv versions are the same as on the laptop, so a later rebuild uses the tested versions.
- **`/frontend/dist`:** `main.py` is `/app/app/main.py` and finds the build two folders up, as on the laptop. No setting is needed.

The first build waits for `.dockerignore` (step 3).

<br>

## 3. Keep the build context small with .dockerignore

- **Before:** no `.dockerignore`. Docker would send the whole root to the builder, including `.env`, `.venv/`, `node_modules/` and `.git/`.
- **Why the change:** every file in the build context can end up in an image layer, secrets included.

[.dockerignore](.dockerignore) is an allow list:

| Lines                                                                        | Do                                                                             |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `*`                                                                          | Ignores everything                                                             |
| `!backend/pyproject.toml`, `!backend/uv.lock`, `!backend/app/`, `!frontend/` | Let in only what the Dockerfile copies                                         |
| `frontend/node_modules/`, `frontend/dist/`, `**/__pycache__/`                | Stay out: stage 1 installs and builds them itself                              |
| `**/.env*`                                                                   | Stays out: Vite would write the values of a frontend `.env` into the JS bundle |

Build the image and look inside it, in the repository root:

```bash
docker build --platform linux/amd64 -t content-hub .
docker run --rm content-hub ls /frontend/dist /app
```

**Expected result:**

| Check                  | Result                                | Shows                                                 |
| ---------------------- | ------------------------------------- | ----------------------------------------------------- |
| `transferring context` | A few hundred kB                      | `node_modules/` and `.venv/` stayed on the laptop.    |
| `/frontend/dist`       | `assets`, `favicon.svg`, `index.html` | Stage 1 built the React app, and stage 2 received it. |
| `/app`                 | `app`, `pyproject.toml`, `uv.lock`    | The backend code and its lock files are in the image. |

<br>

## 4. Run the image with Compose

- **Before:** Compose ran only the database. The app ran with `uv run fastapi dev` and reached the database on `localhost`.
- **Why the change:** the image must work against a database on the laptop before it goes to Cloud Run.

[docker-compose.yaml](docker-compose.yaml):

| Part                                   | Does                                                                                                     |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `app` service, `build: .`              | Builds the image from the Dockerfile                                                                     |
| `DATABASE_URL` with the host `db`      | Compose services reach each other by service name; `localhost` is the container itself                   |
| `127.0.0.1:8080:8080`                  | Publishes the app on the laptop only                                                                     |
| `healthcheck` on `db` and `depends_on` | The app starts only when PostgreSQL accepts connections, because the lifespan opens the pool at start-up |
| `image: postgres:18.7`                 | An exact tag, as in the Dockerfile                                                                       |

Run both services, in the repository root:

```bash
docker compose up --build
```

**Expected result:**

| Check                                       | Result                                                | Shows                                                |
| ------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------- |
| The log                                     | `db` is healthy before `Application startup complete` | The app waits for the database.                      |
| `http://localhost:8080` in the browser      | The home page                                         | The image serves the React files.                    |
| Reload `http://localhost:8080/blog/1`       | The post, not a `404`                                 | The fallback to `index.html` works in the image too. |
| `curl -i http://localhost:8080/api/unknown` | `404` with `{"detail":"Not Found"}`                   | Unknown API paths still get a JSON error.            |
| `docker compose exec db postgres --version` | `postgres (PostgreSQL) 18.7`                          | The pinned image runs.                               |
