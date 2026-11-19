# Notes: GCP deployment with Terraform

The build log of the deployment, step by step. The commands to deploy are in [runbook.md](docs/runbook.md).

The app (FastAPI, PostgreSQL and the React frontend) runs as one Cloud Run service that serves both the API and the React files, with Cloud SQL as the database. Terraform creates every resource.

<br>

## 1. Serve the React build from FastAPI

- [main.py](backend/app/main.py) serves `frontend/dist/` after every API route.
- `app.mount("/assets", StaticFiles(...))` serves the hashed JS and CSS files.
- `serve_frontend` on `/{path:path}`, added last: a file from the root of `dist/` (such as `favicon.svg`), JSON `404` for an unknown `/api` path, `index.html` for any other path.

<br>

## 2. Build the image with a multi-stage Dockerfile

- [Dockerfile](Dockerfile) in the repository root, because the image needs `frontend/` and `backend/`.
- Stage 1, `node:24.14.0-slim`: `npm ci` and `npm run build`; only `dist/` leaves it.
- Stage 2, `python:3.14.10-slim`: `uv sync --locked --no-dev`, then `backend/app` and the build in `/frontend/dist`.
- `CMD` starts `fastapi run` on port `8080`.

<br>

## 3. Keep the build context small with .dockerignore

- [.dockerignore](.dockerignore) is an allow list: `*` ignores everything.
- Let in: `backend/pyproject.toml`, `backend/uv.lock`, `backend/app/`, `frontend/`.
- Kept out: `frontend/node_modules/`, `frontend/dist/`, `**/__pycache__/`, `**/.env*`.

<br>

## 4. Run the image with Compose

- [docker-compose.yaml](docker-compose.yaml) has a second service, `app`, built from the Dockerfile.
- `DATABASE_URL` uses the host `db`, the service name.
- The app is published on `127.0.0.1:8080`.
- A `pg_isready` healthcheck on `db` and `depends_on: condition: service_healthy` make the app wait for the database.
- `db` uses the exact tag `postgres:18.7`.

<br>

## 5. Seed with psql's \copy

- The 12 `COPY` lines in [02-seed.sql](db/init/02-seed.sql) became `\copy`, with the same paths and options and no `;` at the end.
- The same script now loads the CSV files locally and on Cloud SQL.

<br>

## 6. Prepare Terraform: the Part A request and the skeleton

- Two APIs enabled once, by hand, on Part A's project:

  ```bash
  gcloud services enable sqladmin.googleapis.com secretmanager.googleapis.com --project=<project-id>
  ```

- [terraform/](terraform/): `environments/dev/` (provider, backend, module call) and `modules/content_hub/` (the resources).
- Terraform `~> 1.16` and the `google` provider `~> 8.6`; the lock file is committed.
- The state lives in Part A's bucket under the prefix `content-hub`; the bucket name comes from a git-ignored `backend.hcl`.
- The project ID comes from a git-ignored `terraform.tfvars`; both files have an `.example` copy.

<br>

## 7. Define the database, secret, identity and registry

One file per concern in [modules/content_hub/](terraform/modules/content_hub/):

- [sql.tf](terraform/modules/content_hub/sql.tf): PostgreSQL 18, Enterprise edition, `db-f1-micro`, no backups, `deletion_protection = false`; the name `content-hub-db-<8 random characters>`; the database and user `content_hub`, with a generated 32-character password and `deletion_policy = "ABANDON"` on the user.
- [secrets.tf](terraform/modules/content_hub/secrets.tf): the secret `content-hub-database-url`, holding `postgresql://<user>:<password>@/<db>?host=/cloudsql/<connection-name>`.
- [iam.tf](terraform/modules/content_hub/iam.tf): the service account `content-hub-app`, with `cloudsql.client` on the project and `secretAccessor` on the one secret.
- [registry.tf](terraform/modules/content_hub/registry.tf): the Docker repository `content-hub`.
- [outputs.tf](terraform/modules/content_hub/outputs.tf): `registry_uri`, `sql_connection_name`, `service_account_email`.
- The `random` provider (`~> 3.7`) for the password and the name suffix.
- [tests/](terraform/modules/content_hub/tests/): one `terraform test` file per concern, against a mocked Google provider.

<br>

## 8. Send the session cookie over HTTPS only

- `secure=True` on `set_cookie` and `delete_cookie` in [mock_session.py](backend/app/mock_session.py).

<br>

## 9. Define the Cloud Run service

- [run.tf](terraform/modules/content_hub/run.tf): the service `content-hub`, running `<registry_uri>/content-hub:<image_tag>` as `content-hub-app`, on port `8080`.
- `DATABASE_URL` from the exact secret version; the Cloud SQL socket mounted on `/cloudsql`; at most one instance; `deletion_protection = false`.
- `run.invoker` for `allUsers`: the site is public.
- A third input, `image_tag`, set in `terraform.tfvars`.
- The output `service_url`, and [tests/run.tftest.hcl](terraform/modules/content_hub/tests/run.tftest.hcl).

<br>

## 10. Deploy to GCP and remove it again

- The steps of the run: [runbook.md](docs/runbook.md).
- The records of the real run: [docs/real-run/](docs/real-run/README.md).
