# Deployment roadmap: GCP with Terraform (phased approach)

This roadmap takes the app at tag `v0.3.0` from the laptop to GCP. Each phase ends with a check the maintainer runs. The API contract in [api_endpoints.md](./api_endpoints.md) does not change; only how the app is packaged, configured and hosted.

> **Draft:** versions, machine types and prices below are from planning. Check each one against the official documentation at its step.

<br>

## Target architecture

| Part                                       | GCP service                                     | Created by                                                                              |
| ------------------------------------------ | ----------------------------------------------- | --------------------------------------------------------------------------------------- |
| **FastAPI and the built React app**        | **Cloud Run**: one service, one container       | Terraform (this repo)                                                                   |
| **PostgreSQL**                             | **Cloud SQL** for PostgreSQL                    | Terraform (this repo)                                                                   |
| **`DATABASE_URL`**                         | **Secret Manager**                              | Terraform (this repo)                                                                   |
| **Container images**                       | **Artifact Registry**: a Docker repository      | Terraform (this repo)                                                                   |
| **Runtime identity**                       | A **service account** for the Cloud Run service | Terraform (this repo)                                                                   |
| **Project, billing, budget, state bucket** | Part A of the pipeline project                  | Already up (`scripts/bootstrap.sh` in the pipeline repository)                          |
| **2 extra APIs**                           | `sqladmin`, `secretmanager`                     | One `gcloud` command: a Part A request, run by hand and recorded in this repo's runbook |

- **One origin:** FastAPI serves both `/api/...` and the React files. The frontend keeps its relative URLs, the session cookie keeps `samesite="lax"`, and no CORS is needed. In development, the Vite proxy still gives the same single origin.
- **Region:** `europe-west1`, the same as Part A.
- **Part A and Part B:** this app is a second feature on the platform of the pipeline project ([decisions.md](../../../gcp-content-intelligence-platform_implementation/docs/decisions.md)). It adds its own resources and two APIs; it changes nothing that Part A created, and the pipeline repository stays unchanged.

<br>

## What stays and what changes

| Area                          | Change                                                                                       |
| ----------------------------- | -------------------------------------------------------------------------------------------- |
| **Routes, models, queries**   | None                                                                                         |
| **`db.py` settings**          | None: `pydantic-settings` reads `DATABASE_URL` from the environment when there is no `.env` |
| **`main.py`**                 | Serves the built React files, with a fallback to `index.html` for client-side routes         |
| **`mock_session.py`**         | None required; the `sessions` dict needs exactly one Cloud Run instance                      |
| **`db/init/02-seed.sql`**     | Server-side `COPY` becomes client-side `\copy`                                               |
| **Frontend code**             | None: `npm run build` already writes static files to `frontend/dist/`                        |
| **New files**                 | `Dockerfile`, `.dockerignore`, `terraform/`, a deployment runbook                            |
| **`docker-compose.yaml`**     | A second service, `app`, to run the image locally before it goes to GCP                      |

<br>

## Branches

One topic per branch, as in [writer_commits.md](../../.claude/rules/writer_commits.md). Two long-lived branches start from `main` at tag `v0.3.0`.

| Branch                   | Role                                                                                         |
| ------------------------ | -------------------------------------------------------------------------------------------- |
| `feature/gcp-deployment` | The integration branch: every deployment branch merges into it; the deployment runs from it |
| `release/v0.3.0`         | The local app without the deployment, kept for maintenance                                  |

- **Deployment branches:** each one starts from an up-to-date `feature/gcp-deployment` after the previous one is merged. Its pull request targets `feature/gcp-deployment`, not `main`.
- **Merge commits:** no squash, so each branch keeps its own commits.
- **Final merge:** `feature/gcp-deployment` merges into `main` when the deployment works end to end. GitHub closes an issue (`Closes #<number>`) only on a merge into `main`.

| Phase  | Branch                              | Commit types inside              | Holds                                                                                 |
| ------ | ----------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------- |
| Set-up | `chore/deployment-setup`            | `chore(claude)`, `docs`, `ops`   | Rules, settings, this roadmap and the CI push filter                                  |
| 1      | `chore/docker-image`                | `feat(backend)`, `build`, `docs` | Steps 1–4: `main.py` serves `dist/`, `Dockerfile`, `.dockerignore`, the `app` service |
| 2, 3   | `chore/seed-and-terraform-skeleton` | `refactor`, `ops`, `docs`        | `02-seed.sql` with `\copy`; `terraform/`: environment, backend, empty module          |
| 4      | `chore/terraform-database`          | `ops`                            | Cloud SQL, secret, service account, Artifact Registry                                 |
| 5      | `feature/secure-cookie`             | `feat(backend)`                  | `secure=True` on the session cookie                                                   |
| 5      | `chore/terraform-cloud-run`         | `ops`                            | The Cloud Run service and its public access                                           |
| 6      | `chore/deployment-runbook`          | `docs`                           | The runbook: Part A request, push, seed, checks, destroy                              |

- **No scope for root files:** `Dockerfile`, `docker-compose.yaml`, `db/` and `terraform/` are outside `backend/` and `frontend/`, so their commits have no scope.
- **`ops` for Terraform:** infrastructure and deployment, as in Conventional Commits.
- **Phase 7:** no branch; the destroy commands go into the runbook of Phase 6.

<br>

## Phase 1: one image, run locally

**Goal:** the same container that Cloud Run will run works on the laptop against the Compose database.

**Branch:** `chore/docker-image` (steps 1–4). The build log is in [NOTES_DEPLOYMENT.md](../../NOTES_DEPLOYMENT.md).

### Steps

1. **Serve the React build from FastAPI:** a `StaticFiles` mount for the files in `dist/`, and a fallback that answers `index.html` for any other non-`/api` path. `BrowserRouter` owns paths such as `/blog/3`; without the fallback, a page reload there answers `404`. An unknown `/api/...` path must still answer FastAPI's JSON `404`, not the HTML page. Concept: mounting a sub-application, and route order.
2. **`Dockerfile` (multi-stage, in the repository root):** a Node stage builds the frontend; the Python stage installs the backend with `uv` and copies `dist/` in. The build context is the root because the image needs both `frontend/` and `backend/`. Concept: build stages keep Node and `node_modules` out of the final image.
3. **`.dockerignore`:** an allow list: it ignores everything, then lets in only the paths the Dockerfile copies. `.env`, `.venv/`, `node_modules/`, `.git/` and the caches stay out of the build context. Concept: the build context is everything Docker can copy; a secret in it can end up in an image layer.
4. **`app` service in `docker-compose.yaml`:** builds the image, publishes port `8080` on `127.0.0.1`, and sets `DATABASE_URL` with the host `db` instead of `localhost`. A `pg_isready` healthcheck on `db` and `depends_on: condition: service_healthy` make the app wait for the database, because the lifespan opens the pool at start-up. Concept: Compose services reach each other by service name.

### Image layout

- **Exact tags:** `node:24.14.0-slim`, `python:3.14.10-slim` and the uv image `0.13.7`, the same versions as on the laptop.
- **Build folder:** the image copies `dist/` to `/frontend/dist`. `main.py` is `/app/app/main.py` and finds the build two folders up, as on the laptop, so no setting is needed.
- **The finished file:** [Dockerfile](../../Dockerfile).

### Maintainer check

- `docker compose up --build` in the root; `http://localhost:8080` shows the home page.
- A reload on `/blog/1` shows the post, not a `404`.
- `curl -i http://localhost:8080/api/unknown` answers `404` with `{"detail":"Not Found"}`.
- `http://localhost:8080/docs` still works.

<br>

## Phase 2: a seed script that works on Cloud SQL

**Goal:** one seed file that loads the CSV files into both the local container and Cloud SQL.

**Branch:** `chore/seed-and-terraform-skeleton`, shared with Phase 3. The build log is step 5 in [NOTES_DEPLOYMENT.md](../../NOTES_DEPLOYMENT.md).

- **The problem:** `COPY ... FROM '/seed/...'` makes the **server** read a file on its own disk. That needs superuser rights or the `pg_read_server_files` role; Cloud SQL grants neither. Cloud SQL has no `/docker-entrypoint-initdb.d` either.
- **The fix:** psql's `\copy` makes the **client** read the file and send it over the connection. The options (`FORMAT csv, HEADER MATCH`) stay the same.
- **Local:** the Postgres image runs the `*.sql` init files with psql, so `\copy` works there too. The paths stay `/seed/...`.
- **Cloud SQL (Phase 6):** psql runs in a throwaway `postgres:18.7` container with `db/seed` mounted on `/seed`, connected through the Cloud SQL Auth Proxy. The same `/seed/...` paths work, and the laptop needs no psql of the right version.

### Maintainer check

- `docker compose down -v`, then `docker compose up`: the init log shows the same row counts as before.

<br>

## Phase 3: Part A request and the Terraform skeleton

**Goal:** an empty Terraform configuration that initialises against Part A's state bucket.

**Branch:** `chore/seed-and-terraform-skeleton`, shared with Phase 2. The Part A request is a command, not a commit; the runbook (Phase 6) records it.

### Steps

1. **Part A request (once, by hand, from this repo):**

   ```bash
   gcloud services enable sqladmin.googleapis.com secretmanager.googleapis.com --project=<project-id>
   ```

   Part A is a `gcloud` script with no Terraform state, so this command conflicts with nothing in the pipeline repository. Enabling an API only adds to the project, and running the command again changes nothing. A `google_project_service` resource is not used: `terraform destroy` would turn the API off for the whole project.

2. **Layout, the same as the pipeline project:**

   ```text
   terraform/
   ├── environments/dev/   # provider, backend (prefix "content-hub"), module call, tfvars
   └── modules/content_hub/ # every resource of this app
   ```

3. **Versions:** Terraform `~> 1.16` and the `google` provider `~> 8.6` in the environment, as in the pipeline project. The module states minimum versions only.
4. **Backend:** the `gcs` backend with `bucket` from a git-ignored `backend.hcl` and `prefix = "content-hub"`. The pipeline's state lives under `content-pipeline` in the same bucket, so the two never touch.
5. **Inputs:** `project_id` and `region`, nothing else.

### Maintainer check

- `terraform init -backend-config=backend.hcl` in `terraform/environments/dev/`; `terraform plan` shows no changes.

<br>

## Phase 4: database, secret and identity

**Goal:** Cloud SQL runs, and the app's service account can read the connection URL and connect.

**Branch:** `chore/terraform-database`.

### Resources

| Resource                                     | Settings that matter                                                                                                  |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `google_sql_database_instance`               | `POSTGRES_18` (check availability; else `POSTGRES_17`), edition `ENTERPRISE`, the smallest shared-core tier, `deletion_protection = false` so `terraform destroy` works |
| `google_sql_database`, `google_sql_user`     | The app's database and user                                                                                           |
| `random_password`                            | The user's password (`hashicorp/random` provider)                                                                     |
| `google_secret_manager_secret` and a version | `DATABASE_URL` with the Unix socket host: `postgresql://<user>:<password>@/<db>?host=/cloudsql/<connection-name>`     |
| `google_service_account`                     | The identity of the Cloud Run service                                                                                 |
| IAM grants                                   | `roles/cloudsql.client` on the project; `roles/secretmanager.secretAccessor` on the one secret                        |
| `google_artifact_registry_repository`        | A Docker repository for the app image                                                                                 |

- **Public IP, no authorised networks:** Cloud Run and the Auth Proxy connect through Google's authenticated tunnel, so no network is opened to the internet and no VPC is needed.
- **The socket URL:** asyncpg accepts the socket folder as the `host` query parameter, so `db.py` needs no change.

### Maintainer check

- `terraform apply`; then `terraform plan` shows no changes.
- Console: the instance is running; the secret has one version.

<br>

## Phase 5: image and Cloud Run

**Goal:** the app answers on its Cloud Run URL.

**Branches:** `feature/secure-cookie` (before the image is built), then `chore/terraform-cloud-run`.

### Steps

1. **Build and push the image (by hand):** `docker build --platform linux/amd64`, then `docker push` to Artifact Registry after `gcloud auth configure-docker europe-west1-docker.pkg.dev`. The pushed image is the one tested in Phase 1.
2. **`google_cloud_run_v2_service`:**
   - the image tag from a variable;
   - the service account from Phase 4;
   - `DATABASE_URL` as an environment variable from the secret (`value_source.secret_key_ref`);
   - a `cloud_sql_instance` volume mounted on `/cloudsql`;
   - `scaling.max_instance_count = 1`, because the mock sessions live in one process's memory;
   - `deletion_protection = false`.
3. **Public access:** `google_cloud_run_v2_service_iam_member` with `roles/run.invoker` for `allUsers`.
4. **Output:** the service URL.

- **First deployment order:** Phase 4 creates the registry, this phase pushes the image, then the Cloud Run resource is added. After a full `terraform destroy`, the order matters again: the registry must exist and hold the image before Cloud Run is created.
- **Start-up check for free:** the lifespan opens the pool before the first request. A wrong `DATABASE_URL` or a missing grant makes the revision fail to start, and the error appears in the Cloud Run logs.

### Maintainer check

- `curl -i <service-url>/api/tags` answers `200` with an empty list (Phase 6 loads the data).
- The home page loads in the browser.

<br>

## Phase 6: schema, seed and a full check

**Goal:** the deployed app works end to end with the seed data.

**Branch:** `chore/deployment-runbook`.

### Steps

1. **Cloud SQL Auth Proxy on the laptop:** `cloud-sql-proxy --port 5433 <connection-name>`. Port `5433`, because the Compose database already uses `5432`.
2. **Schema and seed:** run `01-schema.sql`, then `02-seed.sql`, with psql in a `postgres:18.7` container on the host network, `db/` mounted read-only.
3. **Runbook:** each command, in order, in a committed runbook, as in the pipeline project.

### Maintainer check

- `curl -i <service-url>/api/blog` answers `200` with the seed posts.
- In the browser: mock login, create, edit and delete a post, logout.
- `curl -i <service-url>/api/me` without a cookie answers `401` with `{"detail":"Not signed in"}`.

<br>

## Phase 7: stop the cost

**Goal:** nothing costs money when the app is not in use.

- **`terraform destroy`** removes every resource of this app. Part A stays up.
- **Never `gcloud projects delete`:** it would also remove Part A and the pipeline's state.
- **Pause instead of destroy (optional):** Cloud SQL's `activation_policy = "NEVER"` stops the instance but keeps the data; storage is still charged.

<br>

## Cost estimate

| Service               | Expected cost                                                                  |
| --------------------- | ------------------------------------------------------------------------------ |
| **Cloud SQL**         | The only real cost: about 9–12 USD a month for the smallest instance and its disk |
| **Cloud Run**         | Free tier                                                                      |
| **Artifact Registry** | Free up to 0.5 GB                                                              |
| **Secret Manager**    | Free tier                                                                      |

- **Budget:** Part A's budget is 10 a month, so the 50 % and 90 % alerts are expected while Cloud SQL runs. It only alerts; it never stops spending.
- **Free Trial:** the credit pays for all of it. Check its end date under Billing before starting Phase 4.

<br>

## Later, outside this roadmap

- **Deploy from GitHub Actions** (`chore/deploy-workflow`): build, push and `terraform apply` on merge to `main`, with Workload Identity Federation instead of a stored key.
- **Terraform checks in CI** (`chore/terraform-checks`): `terraform fmt -check`, `terraform validate`, TFLint and `terraform test` with a mocked provider, as in the pipeline project.
- **Real sign-in:** replaces the mock session; then more than one Cloud Run instance is possible.

<br>

## Decisions to confirm

Each has a recommendation; the maintainer confirms it at its phase.

| Decision                    | Recommendation                                           | Reason                                                                                                   |
| --------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Frontend hosting**        | One container; FastAPI serves `dist/` (confirmed)        | One origin: no CORS, the cookie works unchanged, one Cloud Run service                                   |
| **Terraform folder**        | `terraform/` in the repository root                      | The same layout as the pipeline project                                                                  |
| **Database password**       | `random_password` in Terraform                           | No hand-made secret. The password is stored in the state; the state bucket is private and versioned. Write-only arguments can remove it from the state later |
| **Image build**             | Local `docker build` and `docker push`                   | The image tested in Phase 1 is the one deployed; Cloud Build adds its own service account permissions   |
| **Secure cookie**           | Add `secure=True` to the session cookie                  | Cloud Run serves only HTTPS; browsers still accept a secure cookie on `http://localhost`                 |
