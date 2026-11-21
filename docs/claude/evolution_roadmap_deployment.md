# Deployment roadmap: GCP with Terraform (phased approach)

This roadmap takes the app at tag `v0.3.0` from the laptop to GCP. Each phase ends with a check the maintainer runs. GCP resources are created only once, in Phase 5; every check before it creates nothing and is free.

<br>

## From the laptop to GCP

**On the laptop, three separate processes run the app:** Vite serves the frontend, `fastapi dev` runs the backend, and Docker Compose runs only the database. **On GCP, each job gets a Google service, and Terraform creates them.** The frontend and the backend share one: they travel together in one image.

### Where everything lives

| What                             | On the laptop                                                            | On GCP                                                                                                                                                     |
| -------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Frontend** (React)             | Vite dev server: `npm run dev`, port `5173`                              | **Inside the app container on Cloud Run.** No service of its own: FastAPI serves the built files.                                                          |
| **Backend** (FastAPI)            | `uv run fastapi dev app/main.py`, port `8000`                            | **Cloud Run**: runs the container                                                                                                                          |
| **Database server** (PostgreSQL) | `postgres:18.7` container: `docker compose up -d db`                     | **Cloud SQL**: Google runs PostgreSQL                                                                                                                      |
| **Database data**                | Docker volume `pgdata`                                                   | **The Cloud SQL disk** (10 GB)                                                                                                                             |
| **Tables and seed data**         | Created automatically from `db/init/` when the volume is empty           | **Loaded once by hand:** `psql` through the Cloud SQL Auth Proxy (runbook)                                                                                 |
| **`.env` file**                  | A file in the repository root                                            | **No file.** `DATABASE_URL` sits in **Secret Manager**; Cloud Run passes it to the app as an environment variable. Terraform generates the password.       |
| **Docker image**                 | Docker's image store on the laptop                                       | **Artifact Registry**                                                                                                                                      |
| **Source code**                  | The repository                                                           | **Stays on GitHub.** Only the image goes to GCP.                                                                                                           |
| **Address of the app**           | `http://localhost:5173` (Vite forwards `/api` to the backend)            | `https://content-hub-....run.app`; HTTPS comes automatically                                                                                               |
| **Connection to the database**   | `localhost:5432`, the port Compose publishes                             | **A Unix socket** in `/cloudsql`, set up by Cloud Run                                                                                                      |
| **Who the app is**               | Nobody: it runs as you, on your laptop                                   | **A service account**, `content-hub-app`: it may read one secret and connect to Cloud SQL                                                                  |
| **Logs**                         | The terminals of `fastapi dev` and Compose                               | **Cloud Logging**: the Cloud Run "Logs" tab                                                                                                                |
| **Start and stop**               | Start and stop each process                                              | `terraform apply` and `terraform destroy`; Cloud Run also stops by itself when idle                                                                        |
| **Description of the set-up**    | `docker-compose.yaml` (the database only) and the README commands        | `terraform/`                                                                                                                                               |
| **Memory of the set-up**         | Not needed                                                               | **Terraform state** in Part A's bucket                                                                                                                     |
| **Mock sessions**                | The backend's memory; lost when `fastapi dev` reloads after a saved file | The memory of the **one** Cloud Run instance (`max_instance_count = 1`); lost when the instance stops: after about 15 minutes idle, or on a new deployment |

### Why the frontend and the backend share one container

**The built frontend is only files.** `npm run build` turns the React code into `index.html`, JavaScript and CSS in `frontend/dist/`. Vite is a development tool; on GCP, nothing of it is needed. The files only need **something that hands them to the browser**, and FastAPI already runs, so it does that job too (the `main.py` change).

What one container gives this app:

- **One origin, so no frontend change:** the website and the API share one address (`https://content-hub-....run.app`). Browsers block calls between different origins unless the server allows them (CORS), and send cookies across origins only with extra settings. With one origin, the frontend keeps `fetch("/api/...")`, the session cookie keeps `samesite="lax"`, and no CORS code is needed. Locally, Vite's proxy creates the same situation.
- **One image, one deployment:** the frontend and the backend always run in matching versions. One `docker build`, one `docker push`, one `image_tag`.
- **One service in Terraform:** one Cloud Run service, one URL, no extra resources to create, pay for and destroy.

The alternatives, and why not here:

| Alternative                                                         | What it would need                                                                                                                                                                           |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A second Cloud Run service** for the frontend (for example nginx) | Two origins: CORS in FastAPI, a cross-site cookie (`samesite="none"`), an absolute API URL in the frontend; or a load balancer to put both under one domain. Two images to build and deploy. |
| **A Cloud Storage bucket** for the files, with a CDN                | A load balancer to share one domain with the API, which has a fixed monthly cost; more Terraform resources.                                                                                  |
| **Firebase Hosting** with a rewrite of `/api` to Cloud Run          | One origin is possible, but it adds another product and another deploy tool.                                                                                                                 |

**When splitting is worth it:** high traffic, where a CDN serves the files faster and cheaper than FastAPI; separate teams; or a frontend that deploys much more often than the backend. None of these applies to a learning project with one maintainer.

**The trade-off accepted:** every frontend change rebuilds the whole image, and FastAPI serves the files less efficiently than a CDN. For this app, neither matters.

### The same, grouped by job

- **Things that run (2):** Cloud Run (frontend and backend) and Cloud SQL (database). Only these two need their own instance; Cloud SQL is the one that costs most.
- **Things that store (3):** Artifact Registry (the image), Secret Manager (`DATABASE_URL`), the state bucket (Terraform's memory).
- **Things that allow (1):** the service account and its two roles.
- **Things that stay on the laptop:** the code, Docker for building the image, and `psql` with the Auth Proxy for the seed.

### The step between: the image on the laptop

Before the image goes to GCP, it runs on the laptop: `docker compose up --build` starts the database **and** the app container, at `http://localhost:8080`. This is the only time Compose runs more than the database. It tests the exact image that Cloud Run will run.

### What changes in the code

Only what GCP forces; the routes, models and queries stay as they are.

- **`main.py`:** serves the built React files, with a fallback to `index.html` for client-side routes. On GCP, no Vite server exists.
- **`02-seed.sql`:** server-side `COPY` (the server reads the CSV file from its own disk) becomes client-side `\copy` (psql reads the file and sends the rows over the connection). On Cloud SQL, the files cannot be put on the server's disk, and `COPY` from a file needs superuser rights that Cloud SQL does not grant.
- **`mock_session.py`:** `secure=True` on `set_cookie` and `delete_cookie`: Cloud Run serves only HTTPS, and browsers still accept a Secure cookie on `http://localhost`, so local development keeps working. The `sessions` dict stays in the process's memory, so Terraform limits Cloud Run to one instance.
- **`docker-compose.yaml`:** a second service, `app`, for the image test; a healthcheck on `db`; the exact `postgres:18.7` tag.
- **New files:** `Dockerfile`, `.dockerignore`, `terraform/`, the runbook.
- **No change:** `db.py` (`pydantic-settings` reads `DATABASE_URL` from the environment when there is no `.env`) and the frontend code (`npm run build` already writes `frontend/dist/`).

### The mock session on Cloud Run

The code is the same as on the laptop: the session IDs live in a dict in the server's memory, and the browser keeps the ID in a cookie.

- **One instance:** a second instance would have its own dict and would not know the logins of the first. So Cloud Run runs at most one.
- **Lost when the instance stops:** after about 15 minutes without a request, or on a new deployment. The next request starts an empty instance, so log in again.
- **Public:** anyone who opens `<service-url>/docs` can log in as a staff member and change posts. Acceptable only because the app runs for a short check, holds seed data, and is destroyed right after.

### Who creates what

- **Terraform (this repo):** Cloud Run, Cloud SQL, Secret Manager, Artifact Registry, the service account.
- **Part A (pipeline repository, already up):** the project, billing, the budget, the state bucket (`scripts/bootstrap.sh`).
- **By hand, once:** the 2 extra APIs, `sqladmin` and `secretmanager`. One `gcloud` command, a Part A request, recorded in this repo's runbook.

### Ground rules

- **One container, one origin:** FastAPI serves both `/api/...` and the React files; never add CORS, a second frontend service or absolute API URLs. The reasons are in "Why the frontend and the backend share one container" above.
- **Region:** `europe-west1`, the same as Part A.
- **Part A and Part B:** this app is a second feature on the platform of the pipeline project ([decisions.md](../../../gcp-content-intelligence-platform_implementation/docs/decisions.md)). It adds its own resources and two APIs; it changes nothing that Part A created, and the pipeline repository stays unchanged.

<br>

## Branches

One topic per branch, as in [writer_commits.md](../../.claude/rules/writer_commits.md). Two long-lived branches start from `main` at tag `v0.3.0`.

| Branch                         | Role                                                                                                      |
| ------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `feature/cloud-run-deployment` | The integration branch: every deployment branch merges into it; the deployed image is built from its code |
| `release/v0.3.0`               | The local app without the deployment, kept for maintenance                                                |

- **Deployment branches:** each one starts from an up-to-date `feature/cloud-run-deployment` after the previous one is merged. Its pull request targets `feature/cloud-run-deployment`, not `main`.
- **Merge commits:** no squash, so each branch keeps its own commits.
- **Final merge:** `feature/cloud-run-deployment` merges into `main` when the deployment works end to end. GitHub closes an issue (`Closes #<number>`) only on a merge into `main`.

### Deployment branches in order

| Phase | Branch                     | Content                                                                                                                                                                                           |
| ----- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | `chore/deployment-plan`    | The roadmap; the cloud engineer rules; Terraform and gcloud rules in `settings.json`; backend and commit rules; CI on pushes to `feature/cloud-run-deployment`; `CLAUDE.md`                       |
| 2     | `chore/container-image`    | Serve the React build with a fallback to `index.html`; Secure session cookie; multi-stage `Dockerfile`; `.dockerignore`; the `app` service and the pinned postgres image in `docker-compose.yaml` |
| 3     | `chore/cloud-sql-seed`     | Load the seed CSV files with psql's `\copy` (`02-seed.sql` and the comment in `docker-compose.yaml`)                                                                                              |
| 4     | `chore/terraform`          | `.gitignore`; skeleton; registry, Cloud SQL, secret, identity, Cloud Run, each with its mocked test; the `terraform` CI job                                                                       |
| 5     | `chore/deployment-records` | The records folder in `.gitignore`; the runbook and its reasons; the real deployment; the records and screenshots; `NOTES_DEPLOYMENT.md`, README and `CLAUDE.md` after the run                    |

- **Build log:** every branch also adds its step to `NOTES_DEPLOYMENT.md`, as a `docs` commit.

<br>

## Phase 1: set-up

**Goal:** the plan and the safety rules are in place before any deployment file exists.

**Branch:** `chore/deployment-plan`

### Build

- **This roadmap:** the target, the phases and their checks.
- **The cloud engineer rules** (`engineer_cloud.md`): how Docker, Terraform and GCP are used in this repo, and where Part A ends.
- **`settings.json`:** Claude may run only the offline checks; `terraform apply`, `destroy`, `docker` and every `gcloud` command that changes the cloud are denied or asked. Idea: the commands that cost money or change the cloud stay with the maintainer.
- **The backend rule** points to this roadmap; **the commit rules** add the `release/` branch and the deployment branches.
- **CI:** runs on pushes to `feature/cloud-run-deployment` too.
- **`CLAUDE.md`:** describes the deployment work.

### Check

- CI runs on the first push to `feature/cloud-run-deployment`.

<br>

## Phase 2: one image, run locally

**Goal:** the same container that Cloud Run will run works on the laptop against the Compose database.

**Branch:** `chore/container-image`

### Build

- **FastAPI serves the React build:** a `StaticFiles` mount for `dist/assets`, and a catch-all route, registered last, that answers `index.html` for client-side paths such as `/blog/3`. An unknown `/api/...` path keeps FastAPI's JSON `404`. Idea: route order decides which handler answers.
- **Secure session cookie:** `secure=True` on `set_cookie` and `delete_cookie`. Idea: Cloud Run serves only HTTPS, and browsers treat `http://localhost` as secure, so development keeps working.
- **`Dockerfile`** (multi-stage, in the repository root): a Node stage builds `dist/`; a Python stage installs the backend with `uv`, copies `dist/` in and runs FastAPI on port `8080`. Exact image tags; built for `linux/amd64`, Cloud Run's platform. Idea: build stages keep Node and `node_modules` out of the final image.
- **`.dockerignore`:** an allow list that lets in only what the `Dockerfile` copies. Idea: the build context is everything Docker can copy; a secret in it can end up in an image layer.
- **The `app` service in `docker-compose.yaml`:** builds the image, publishes `127.0.0.1:8080`, sets `DATABASE_URL` with the host `db`, and waits for a `pg_isready` healthcheck on `db`, because the lifespan opens the pool at start-up. `db` gets the exact `postgres:18.7` tag. Idea: Compose services reach each other by service name.

### Check

- `docker compose up --build`: `http://localhost:8080` shows the home page.
- A reload on `/blog/1` shows the post, not a `404`.
- `curl -i http://localhost:8080/api/unknown` answers `404` with `{"detail":"Not Found"}`.
- `http://localhost:8080/docs` still works.

<br>

## Phase 3: a seed script that works on Cloud SQL

**Goal:** one seed file that loads the CSV files into both the local container and Cloud SQL.

**Branch:** `chore/cloud-sql-seed`

### Build

- `02-seed.sql` uses psql's `\copy` instead of `COPY`; the comment in `docker-compose.yaml` says so. Idea: the client reads the file and sends the rows, so the server needs neither the file nor superuser rights (see "What changes in the code").

### Check

- `docker compose down -v`, then `docker compose up -d db`: the init log shows the row count of every table.

<br>

## Phase 4: the infrastructure as Terraform code

**Goal:** every GCP resource of the app is written in Terraform and passes the offline checks. Nothing is created in GCP yet.

**Branch:** `chore/terraform`. The layout, file names and style follow the Terraform rules in `engineer_cloud.md`.

### Build

One step and one commit at a time, each resource with its mocked test:

1. **The two APIs (a command, not a commit):** the maintainer enables `sqladmin` and `secretmanager` once by hand, because Part A owns the APIs.
2. **Skeleton:** `.gitignore` for values, state and working files; `environments/dev/` (backend, provider, module call) and `modules/content_hub/` with three inputs: `image_tag`, `project_id`, `region`.
3. **Registry** (`registry.tf`): a Docker repository in the Cloud Run region.
4. **Database** (`sql.tf`): PostgreSQL 18 on `db-f1-micro`, no backups, the database and the user `content_hub`.
5. **Secret** (`secrets.tf`): `DATABASE_URL`, with the Cloud SQL socket as its host.
6. **Identity** (`iam.tf`): the service account `content-hub-app`, with only the two roles it needs.
7. **Cloud Run** (`run.tf`): the image by `image_tag`, `DATABASE_URL` from the secret, the Cloud SQL socket, at most one instance (the mock sessions live in memory), public access.
8. **CI** (`ci.yml`): a third job, `terraform`, next to `backend` and `frontend`: `terraform fmt -check -recursive`, `terraform validate` in the environment and `terraform test` in the module, all with `init -backend=false`, Terraform `1.16.x` as on the laptop. Idea: offline checks need no GCP login, so every pull request is checked against the Terraform rules.

- **The mocked tests:** `terraform test` runs the module against a fake Google provider: no GCP call, no cost. They prove the names, arguments and references Terraform would send; what GCP decides itself (permissions, quotas) only the real deployment shows.

### Check

- `terraform fmt -check`, `terraform validate` and `terraform test` pass, on the laptop and in the `terraform` CI job.
- `terraform plan` with the real backend: only additions, `0 to change, 0 to destroy`. No `apply`.

<br>

## Phase 5: the runbook, the real deployment and the records

**Goal:** the deployed app works end to end with the seed data, is removed again, and the run is documented. This is the only phase that creates resources in GCP; the cost runs only from the first `apply` to `destroy`.

**Branch:** `chore/deployment-records`. It changes only docs and `.gitignore`, so one pull request after the run is enough. The runbook stays uncommitted until the run is over, and is then committed once, with the fixes the run showed.

### Build

1. **`.gitignore` first:** the `.build/` line is committed before any command writes a record, because the raw records show the project ID.
2. **The runbook** (`docs/runbook.md`, reasons in `docs/notes/info_runbook.md`): every command in order, with its expected result. The registry is applied first, then the image is pushed, then the rest.
3. **The real deployment:** follow the runbook to `destroy`. The image tag is the commit of `feature/cloud-run-deployment`.
4. **After the run:** the runbook with its fixes, the cleaned records in `docs/real-run/`, `NOTES_DEPLOYMENT.md`, `README.md` and `CLAUDE.md`.

### Check

- **Before the run:** the maintainer reads the whole runbook against the merged Terraform code.
- **During the run:** `curl -i <service-url>/api/blog` answers `200` with the seed posts; the browser flow (login, create, edit, delete, logout) works; after `destroy`, `gcloud sql instances list` is empty.
- **After the run:** no committed file shows the project ID, the project number, an email address or billing details.

### Stop the cost

- **`terraform destroy`** removes every resource of this app. Part A stays up.
- **Never `gcloud projects delete`:** it would also remove Part A and the pipeline's state.
- **Pause instead of destroy (optional):** Cloud SQL's `activation_policy = "NEVER"` stops the instance but keeps the data; the storage is still charged.

<br>

## Cost estimate

| Service               | Expected cost                                                                                               |
| --------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Cloud SQL**         | The only real cost: charged per hour for `db-f1-micro` and a 10 GB disk, only between `apply` and `destroy` |
| **Cloud Run**         | Free tier                                                                                                   |
| **Artifact Registry** | Free up to 0.5 GB                                                                                           |
| **Secret Manager**    | Free tier                                                                                                   |

- **Confirm the Cloud SQL price** with Google's pricing calculator before the real deployment in Phase 5.
- **Budget:** Part A's budget sends alerts while Cloud SQL runs. It only alerts; it never stops spending.
