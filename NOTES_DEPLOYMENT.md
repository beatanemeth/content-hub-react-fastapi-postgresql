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
