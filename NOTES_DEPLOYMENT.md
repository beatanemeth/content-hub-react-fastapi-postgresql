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
  5. [Seed with psql's \copy](#5-seed-with-psqls-copy)
  6. [Prepare Terraform: the Part A request and the skeleton](#6-prepare-terraform-the-part-a-request-and-the-skeleton)
  7. [Define the database, secret, identity and registry, tested offline](#7-define-the-database-secret-identity-and-registry-tested-offline)
  8. [Send the session cookie over HTTPS only](#8-send-the-session-cookie-over-https-only)
  9. [Define the Cloud Run service, tested offline](#9-define-the-cloud-run-service-tested-offline)

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

<br>

## 5. Seed with psql's \copy

- **Before:** `02-seed.sql` used `COPY ... FROM '/seed/...'`. The PostgreSQL server opened each CSV file on its own disk.
- **Why the change:** reading the server's disk needs superuser rights, and Cloud SQL does not grant them. psql's `\copy` reads the file on the client side and sends the rows over the connection, so the same script works locally and on Cloud SQL.

Branch `chore/seed-and-terraform-skeleton`:

| Part                                       | Change                                                                                    |
| ------------------------------------------ | ----------------------------------------------------------------------------------------- |
| [02-seed.sql](db/init/02-seed.sql)         | The 12 `COPY` lines become `\copy`, with the same paths and options and no `;` at the end |
| [docker-compose.yaml](docker-compose.yaml) | The comment on the `/seed` mount names `\copy`                                            |

- **No `;`:** `\copy` is a psql command, not SQL. psql takes the rest of the line as its arguments, so each `\copy` stays on one line.
- **Local:** the Postgres image runs the init files with psql, so the container itself is the client. The `/seed` paths stay the same.

Recreate the database, in the repository root (the init files run only on an empty volume):

```bash
docker compose down -v
docker compose up db
```

```bash
docker compose logs db | grep -E "running|COPY|ERROR"
```

**Expected result:**

| Check   | Result                                                | Shows                                                      |
| ------- | ----------------------------------------------------- | ---------------------------------------------------------- |
| The log | 12 `COPY <n>` lines, for example `COPY 13` for `post` | Every CSV file loaded, with the same row counts as before. |
| The log | No `ERROR`                                            | The script ran to the end: any error would stop the init.  |

<br>

## 6. Prepare Terraform: the Part A request and the skeleton

- **Before:** the project had no Cloud SQL or Secret Manager API, and the repository had no Terraform.
- **Why the change:** the deployment creates a Cloud SQL instance and a secret, and GCP rejects both while their APIs are off. Terraform also needs a place for its state before it creates anything.

**Part A request**, once, by hand, in any folder:

```bash
gcloud services enable sqladmin.googleapis.com secretmanager.googleapis.com --project=<project-id>
```

Terraform does not turn the APIs on. A `google_project_service` resource would turn them off for the whole project on `terraform destroy`, including for the pipeline.

Branch `chore/seed-and-terraform-skeleton`. [terraform/](terraform/) has the same layout as the pipeline project:

| Part                                   | Does                                                                                               |
| -------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `environments/dev/versions.tf`         | Pins Terraform `~> 1.16` and the `google` provider `~> 8.6`                                        |
| `environments/dev/backend.tf`          | Keeps the state in Part A's bucket under the prefix `content-hub`, apart from the pipeline's state |
| `environments/dev/main.tf`             | Configures the provider and calls the module                                                       |
| `environments/dev/variables.tf`        | `project_id`, and `region` with the default `europe-west1`                                         |
| `environments/dev/.terraform.lock.hcl` | Records the provider version (`8.12.0`), so every `init` installs the same one                     |
| `modules/content_hub/`                 | The two inputs, with no defaults and no resources yet; Phase 4 adds the resources                  |
| [.gitignore](.gitignore)               | Keeps `terraform.tfvars`, `backend.hcl`, `.terraform/` and the state files out of git              |

Two local files hold the real values. Both are git-ignored and start as a copy of their `.example` file:

| File               | Holds                             | Read by                      |
| ------------------ | --------------------------------- | ---------------------------- |
| `terraform.tfvars` | `project_id = "<project-id>"`     | `terraform plan` and `apply` |
| `backend.hcl`      | `bucket = "<project-id>-tfstate"` | `terraform init`             |

`init` connects to the bucket before Terraform reads any variable, so the bucket name needs its own file.

Create the two files, then connect and compare, in `terraform/environments/dev/`:

```bash
cp terraform.tfvars.example terraform.tfvars
cp backend.hcl.example backend.hcl
```

Replace `your-project-id` in both files with the real ID, then:

```bash
terraform init -backend-config=backend.hcl
terraform plan
```

**Expected result:**

| Check                                                        | Result                                       | Shows                                                       |
| ------------------------------------------------------------ | -------------------------------------------- | ----------------------------------------------------------- |
| `gcloud services list --enabled`                             | `sqladmin` and `secretmanager` are listed    | The project can now hold a Cloud SQL instance and a secret. |
| `terraform init`                                             | `Successfully configured the backend "gcs"!` | Terraform reaches Part A's state bucket with your login.    |
| `terraform init` with the placeholder still in `backend.hcl` | `403` on `your-project-id-tfstate`           | The bucket name in `backend.hcl` is wrong, not the login.   |
| `terraform plan`                                             | `No changes.`                                | The skeleton is valid and creates nothing yet.              |
| `git status`                                                 | No `backend.hcl` or `terraform.tfvars`       | The real values stay out of git.                            |

<br>

## 7. Define the database, secret, identity and registry, tested offline

- **Before:** the module had two inputs and no resources.
- **Why the change:** the app needs a PostgreSQL server, a connection URL it can read, an identity to run as, and a place for its image. They are written now but created only in the real deployment (Phase 6): until then, nothing runs in GCP and nothing costs money.

Branch `chore/terraform-database`. One file per concern in [modules/content_hub/](terraform/modules/content_hub/):

| File                                                     | Defines                                                                                                                 |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| [sql.tf](terraform/modules/content_hub/sql.tf)           | A PostgreSQL 18 instance on the smallest tier, the `content_hub` database and user, and the user's generated password   |
| [secrets.tf](terraform/modules/content_hub/secrets.tf)   | The secret `content-hub-database-url`, which holds `DATABASE_URL`                                                       |
| [iam.tf](terraform/modules/content_hub/iam.tf)           | The service account `content-hub-app` and its two roles: connect to Cloud SQL, read the one secret                      |
| [registry.tf](terraform/modules/content_hub/registry.tf) | The Docker repository `content-hub`                                                                                     |
| [outputs.tf](terraform/modules/content_hub/outputs.tf)   | The registry address, the instance connection name and the account email; the environment's `outputs.tf` passes them on |
| `versions.tf` (module and environment)                   | Add the `random` provider, which generates the password and the name suffix on the laptop                               |
| [tests/](terraform/modules/content_hub/tests/)           | One test file per concern, run against a fake Google provider                                                           |
| [.gitignore](.gitignore)                                 | Keeps the module's lock file out of git; only the environment's lock file decides versions                              |

Settings that a later step relies on:

- **Name suffix:** the instance is `content-hub-db-<8 characters>`. Cloud SQL blocks a deleted instance's name for up to a week, so each new deployment needs a new name.
- **The socket URL:** `DATABASE_URL` has no host before the database name. `?host=/cloudsql/<connection-name>` points to the folder that Cloud Run mounts (Phase 5), and asyncpg reads it from there, so `db.py` does not change.
- **The user is abandoned on destroy:** after the seed, the user owns the tables, and PostgreSQL refuses to drop it. `terraform destroy` skips the user, and deleting the instance removes it.

Test the module in `terraform/modules/content_hub/`, then compare with GCP in `terraform/environments/dev/`:

```bash
terraform init -backend=false
terraform test
```

```bash
terraform init -backend-config=backend.hcl
terraform plan
```

**Expected result:**

`terraform test` applies the module to a fake Google provider: it checks what Terraform would send to GCP, not whether GCP accepts it.

| Check                                         | Result                                             | Shows                                                                            |
| --------------------------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------- |
| `terraform test`                              | `Success! 4 passed, 0 failed.`                     | Each file sends the intended names, settings and links between resources.        |
| `terraform test` after `tier = "db-g1-small"` | `sql.tftest.hcl` fails with its own message        | A test notices a changed setting and says which one; undo the change afterwards. |
| `terraform plan`                              | `11 to add, 0 to change, 0 to destroy`, 3 outputs  | The code is valid against the real project, and nothing is created yet.          |
| `git status`                                  | No `.terraform.lock.hcl` in `modules/content_hub/` | The module's lock file stays out of git.                                         |

<br>

## 8. Send the session cookie over HTTPS only

- **Before:** the session cookie had `HttpOnly` and `SameSite=Lax`. The browser would also send it over plain HTTP.
- **Why the change:** Cloud Run serves the app over HTTPS only. With `Secure`, the browser never sends the session ID unencrypted, and the deployed app loses nothing.

Branch `chore/cloud-run`. [mock_session.py](backend/app/mock_session.py):

| Part                             | Change                                                                      |
| -------------------------------- | --------------------------------------------------------------------------- |
| `set_cookie` in `mock_login`     | `secure=True` adds `Secure` to the cookie                                   |
| `delete_cookie` in `mock_logout` | `secure=True` too, so the login and logout headers describe the same cookie |

- **Local development keeps working:** browsers count `http://localhost` as secure, so they accept and send a `Secure` cookie there. The login runs in `/docs`, as in the README.

Build the frontend in `frontend/`, then start the server in `backend/` (the database container must be running):

```bash
npm run build
```

```bash
uv run fastapi dev app/main.py
```

Then log in at `http://localhost:8000/docs` with **POST /api/mock-login** and `{ "person_id": 1 }`.

**Expected result:**

| Check                                                       | Result                                  | Shows                                                    |
| ----------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------- |
| The `set-cookie` response header of the login               | Ends with `Secure`                      | The browser may send this cookie over HTTPS only.        |
| DevTools, **Application** → **Cookies**                     | The session cookie is marked **Secure** | The browser stored the cookie despite the `http://` URL. |
| Add, edit and delete a post at `http://localhost:8000/blog` | Each works; no `Not signed in`          | The browser still sends the cookie on `localhost`.       |
| **POST /api/mock-logout**                                   | `204`, and the cookie is gone           | Logout removes the `Secure` cookie.                      |

<br>

## 9. Define the Cloud Run service, tested offline

- **Before:** the module had the database, the secret, the app's identity and the registry, but nothing that runs the app.
- **Why the change:** Cloud Run runs the image from step 2 and gives it a public HTTPS address. It ties the earlier parts together: the app runs as `content-hub-app`, reads `DATABASE_URL` from the secret, and reaches Cloud SQL through a socket. As in step 7, nothing is created in GCP yet.

Branch `chore/cloud-run`:

| Part                                                                            | Change                                                                                                                                               |
| ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| [run.tf](terraform/modules/content_hub/run.tf)                                  | The service `content-hub`: the image, the service account, `DATABASE_URL` from the secret, the Cloud SQL socket on `/cloudsql`, one instance at most |
| [run.tf](terraform/modules/content_hub/run.tf)                                  | `run.invoker` for `allUsers`: anyone may open the site; writing still needs the session cookie                                                       |
| `variables.tf` and `main.tf`                                                    | A third input, `image_tag`: the tag of the pushed image                                                                                              |
| [terraform.tfvars.example](terraform/environments/dev/terraform.tfvars.example) | Shows the `image_tag` line                                                                                                                           |
| `outputs.tf` (module and environment)                                           | `service_url`, the address of the app                                                                                                                |
| [tests/run.tftest.hcl](terraform/modules/content_hub/tests/run.tftest.hcl)      | Checks the parts above; the other test files pass an `image_tag` too                                                                                 |

Settings that a later step relies on:

- **The image address:** `<registry_uri>/content-hub:<image_tag>`. The image pushed in Phase 6 must have exactly this name and tag.
- **Registry first:** Cloud Run starts the image during `apply`, so the image must already be in the registry. The first deployment creates the registry alone with `terraform apply -target=...`, pushes the image, then runs a full `apply`.
- **The grants come first:** `depends_on` makes Terraform create the two grants before the service, because the first start needs both.

Add the tag to the local values, in `terraform/environments/dev/terraform.tfvars` (any value works for `plan`; no image needs to exist yet):

```hcl
image_tag = "test"
```

Test the module in `terraform/modules/content_hub/`, then compare with GCP in `terraform/environments/dev/`:

```bash
terraform test
```

```bash
terraform plan
```

**Expected result:**

| Check                                                      | Result                                            | Shows                                                                               |
| ---------------------------------------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `terraform test`                                           | `Success! 5 passed, 0 failed.`                    | The service sends the intended image, account, secret, socket and access settings.  |
| `terraform test` after `version = "latest"` in `run.tf`    | `run.tftest.hcl` fails with its own message       | The test notices when the secret version is not pinned; undo the change afterwards. |
| `terraform plan` without `image_tag` in `terraform.tfvars` | Terraform asks for `var.image_tag`                | The tag has no default, so the wrong image cannot run by accident.                  |
| `terraform plan`                                           | `13 to add, 0 to change, 0 to destroy`, 4 outputs | The code is valid against the real project, and nothing is created yet.             |
