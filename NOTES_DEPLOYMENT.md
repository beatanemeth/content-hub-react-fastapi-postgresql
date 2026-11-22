# Notes: GCP deployment with Terraform

The build log of the deployment, step by step.

The app (FastAPI, PostgreSQL and the React frontend) runs as one Cloud Run service that serves both the API and the React files, with Cloud SQL as the database. Terraform creates every resource.

<br>

## Contents

1. [Serve the React build from FastAPI](#1-serve-the-react-build-from-fastapi)
2. [Send the session cookie over HTTPS only](#2-send-the-session-cookie-over-https-only)
3. [Build the image with a multi-stage Dockerfile](#3-build-the-image-with-a-multi-stage-dockerfile)
4. [Keep the build context small with .dockerignore](#4-keep-the-build-context-small-with-dockerignore)
5. [Run the image with Compose](#5-run-the-image-with-compose)
6. [Seed with psql's \copy](#6-seed-with-psqls-copy)
7. [Enable the two APIs](#7-enable-the-two-apis)
8. [Lay out the Terraform code](#8-lay-out-the-terraform-code)
9. [Define the registry](#9-define-the-registry)
10. [Define the database](#10-define-the-database)
11. [Define the secret](#11-define-the-secret)
12. [Define the identity](#12-define-the-identity)
13. [Define the Cloud Run service](#13-define-the-cloud-run-service)
14. [Check the Terraform code in CI](#14-check-the-terraform-code-in-ci)
15. [Deploy to GCP and remove it again](#15-deploy-to-gcp-and-remove-it-again)
16. [Keep blog.http working in every version](#16-keep-bloghttp-working-in-every-version)

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

<br>

## 7. Enable the two APIs

- `gcloud services enable sqladmin.googleapis.com secretmanager.googleapis.com`, once by hand: the APIs belong to Part A, so Terraform never manages them.

<br>

## 8. Lay out the Terraform code

- [.gitignore](.gitignore): `terraform.tfvars`, `backend.hcl`, `.terraform/`, `*.tfstate*`, `*.tfplan` and the module's lock file.
- [environments/dev/](terraform/environments/dev/): Terraform `~> 1.16`, google `~> 8.6`, the `gcs` backend with the prefix `content-hub` (the bucket comes from `backend.hcl`), the provider and the module call, the committed lock file.
- [modules/content_hub/](terraform/modules/content_hub/): minimum versions only, and three inputs without defaults: `image_tag`, `project_id`, `region`.
- `backend.hcl.example` and `terraform.tfvars.example` list the local values.

<br>

## 9. Define the registry

- [registry.tf](terraform/modules/content_hub/registry.tf): the Docker repository `content-hub` in the Cloud Run region.
- The output `registry_uri`, the prefix of the image name for `docker push`.
- [tests/](terraform/modules/content_hub/tests/): one `terraform test` file per concern, against a mocked google provider; the shared mock in `tests/mocks/`.

<br>

## 10. Define the database

- The `random` provider (`~> 3.9`) for the name suffix and the password.
- [sql.tf](terraform/modules/content_hub/sql.tf): PostgreSQL 18, Enterprise edition, `db-f1-micro`, 10 GB, no backups, `deletion_protection = false`; the name `content-hub-db-<8 random characters>`; public IP with no authorised networks.
- The database and user `content_hub`, with a generated 32-character password without special characters and `deletion_policy = "ABANDON"` on the user.
- The output `sql_connection_name`, for the Auth Proxy.

<br>

## 11. Define the secret

- [secrets.tf](terraform/modules/content_hub/secrets.tf): the secret `content-hub-database-url`, holding `postgresql://<user>:<password>@/<db>?host=/cloudsql/<connection-name>`.

<br>

## 12. Define the identity

- [iam.tf](terraform/modules/content_hub/iam.tf): the service account `content-hub-app`, with `cloudsql.client` on the project and `secretAccessor` on the one secret.

<br>

## 13. Define the Cloud Run service

- [run.tf](terraform/modules/content_hub/run.tf): the service `content-hub`, running `<registry_uri>/content-hub:<image_tag>` as `content-hub-app`, on port `8080`.
- `DATABASE_URL` from the exact secret version; the Cloud SQL socket mounted on `/cloudsql`; at most one instance; `deletion_protection = false`.
- `run.invoker` for `allUsers`: the site is public.
- The output `service_url`.

<br>

## 14. Check the Terraform code in CI

- A third job, `terraform`, in [ci.yml](.github/workflows/ci.yml): `terraform fmt -check -recursive`, then `validate` in the environment and `test` in the module, both after `init -backend=false`, with Terraform `1.16.x`.

<br>

## 15. Deploy to GCP and remove it again

- The steps of the run: [runbook.md](docs/runbook.md).
- The records of the real run: [docs/real-run/](docs/real-run/README.md).

<br>

## 16. Keep blog.http working in every version

`blog.http` has stayed in the repository root since v0.1.0. Each tag holds the copy that matches the API of that version, so checking out a tag is enough to test that version by hand.

### The problem

- For the deployment, the session cookie became `Secure` (see [Send the session cookie over HTTPS only](#2-send-the-session-cookie-over-https-only)): the client sends it back over HTTPS only, because Cloud Run serves only HTTPS.
- **Only v0.4.0 has the problem.** The `Secure` flag came with the deployment; v0.1.0 to v0.3.0 do not set it, so their `blog.http` works as it is.
- Browsers treat `http://localhost` as secure, so the React frontend kept working with the `Secure` cookie.
- The REST Client extension does not treat `http://localhost` as secure. It kept the cookie from `POST /api/mock-login`, but did not send it with the next requests to `http://localhost:8000`.
- So, on v0.4.0 before the fix, every signed-in request in `blog.http` (`GET /api/me` and the `POST`, `PUT` and `DELETE` requests) failed with `401 Not signed in`.

### The fix

- A new setting in `Settings` in [db.py](backend/app/db.py): `is_cookie_secure: bool = True`.
- `settings` is now created once, when `db.py` is imported, instead of inside the lifespan. This way, [mock_session.py](backend/app/mock_session.py) can use it in `set_cookie` and `delete_cookie`.
- The local `.env` turns it off with `IS_COOKIE_SECURE=false`. [.env.example](.env.example) has the same line, with a comment.

### Why the deployed cookie stays Secure

- Only the dev server reads `.env`.
- `.dockerignore` keeps `.env` out of the image, and Compose passes only `DATABASE_URL` to the `app` container.
- Cloud Run gets only `DATABASE_URL`, from Secret Manager.
- Without `IS_COOKIE_SECURE`, the default `True` applies, as before the fix.

### Run an older version

| Version | Database                                    | Start the server in |
| ------- | ------------------------------------------- | ------------------- |
| v0.1.0  | None: the posts are in memory               | The project root    |
| v0.2.0  | `docker compose up -d`, in the project root | The project root    |
| v0.3.0  | `docker compose up -d`, in the project root | `backend/`          |
| v0.4.0  | `docker compose up -d`, in the project root | `backend/`          |

- **The server command is the same everywhere:** `uv run fastapi dev app/main.py`. The header comment of each `blog.http` names its folder.
- **Start each version from its own seed data:** run `docker compose down -v` before `docker compose up -d`. Otherwise, the posts created or deleted on another version stay in the database.
- **One `.env` works for every version:** Git does not track it, so the `IS_COOKIE_SECURE=false` line stays after a checkout. Older versions ignore it: v0.2.0 and v0.3.0 read their settings with `extra="ignore"`, and v0.1.0 has no settings.
