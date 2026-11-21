# Runbook: deploy to GCP and remove it again

> The commands of one run, in order. The reasons behind each step are in [info_runbook.md](notes/info_runbook.md), under the same step numbers. The plan is in [evolution_roadmap_deployment.md](claude/evolution_roadmap_deployment.md). The commands change a real GCP project and cost money; the maintainer runs them by hand.

| Part                                               | When                            | Cost                                  |
| -------------------------------------------------- | ------------------------------- | ------------------------------------- |
| [Before you start](#before-you-start)              | Every run                       | None                                  |
| [1. Before the first run](#1-before-the-first-run) | Once per laptop and project     | None                                  |
| [2. Deploy](#2-deploy)                             | Every run                       | Cloud SQL is charged from step 2.6 on |
| [3. Schema and seed](#3-schema-and-seed)           | Every run, after a new instance | Included in the Cloud SQL cost        |
| [4. Check the app](#4-check-the-app)               | Every run                       | Cloud Run stays in the free tier      |
| [5. Remove everything](#5-remove-everything)       | At the end of every run         | Stops the cost                        |

<br>

## Before you start

- **Folder:** every command runs in the **repository root**; `terraform -chdir=terraform/environments/dev` runs Terraform in the environment folder.
- **Two terminals:** the first one runs every step. The second one runs only the Auth Proxy in part 3.
- **Records:** terminal output goes to the git-ignored `.build/real-run/`, screenshots to `.build/real-run/screenshots/`. After each recorded command, `echo "${PIPESTATUS[0]}"` prints `0` on success.
- **Never record the password:** step 3.2 is not captured, and no screenshot shows the secret's value.
- **Before publishing:** hide the project ID, the project number, your email, the billing account ID and the service URL.
- **Before the first screenshot:** dismiss the Free Trial banner and close any billing tab; both show billing details.

**Shell variables:** they live only in the first terminal. In a new terminal, set them again.

| Variable      | Set in   | Holds                                                      |
| ------------- | -------- | ---------------------------------------------------------- |
| `IMAGE`       | Step 2.5 | The full image name, read from the output `registry_uri`   |
| `SERVICE_URL` | Step 2.8 | The Cloud Run URL, read from the output `service_url`      |
| `PROJECT_ID`  | Step 2.9 | The project ID, read from the output `sql_connection_name` |
| `DB_PASSWORD` | Step 3.2 | The database password; removed again in step 3.4           |

<br>

## 1. Before the first run

Skip a step that is already done; each one is safe to run again.

### 1.1 Log in twice

```bash
gcloud auth login
gcloud auth application-default login
```

If both logins ran for an earlier project, check them instead:

```bash
gcloud auth list
gcloud auth application-default print-access-token > /dev/null && echo "ADC ok"
```

Expected: your account with a `*` (active), then `ADC ok`. If either one fails, run that login again.

**Why:** [1.1](notes/info_runbook.md#11-log-in-twice)

### 1.2 Part A request: two more APIs

```bash
gcloud services enable sqladmin.googleapis.com secretmanager.googleapis.com --project=<project-id>
```

If both APIs are already enabled, check them instead:

```bash
gcloud services list --enabled --project=<project-id> | grep -E 'sqladmin|secretmanager'
```

Expected: two lines, each with the API name and its title:

```text
secretmanager.googleapis.com         Secret Manager API
sqladmin.googleapis.com              Cloud SQL Admin API
```

**Why:** [1.2](notes/info_runbook.md#12-part-a-request-two-more-apis)

### 1.3 Local values

Copy the two `.example` files and replace the placeholders. Both copies are git-ignored. `-n` never overwrites a copy that already exists.

```bash
cp -n terraform/environments/dev/terraform.tfvars.example terraform/environments/dev/terraform.tfvars
cp -n terraform/environments/dev/backend.hcl.example terraform/environments/dev/backend.hcl
```

| File               | Holds                                                    | Read by                      |
| ------------------ | -------------------------------------------------------- | ---------------------------- |
| `terraform.tfvars` | `image_tag` (set in step 2.2) and `project_id`           | `terraform plan` and `apply` |
| `backend.hcl`      | `bucket = "<project-id>-tfstate"`, Part A's state bucket | `terraform init`             |

### 1.4 Connect Terraform to the state bucket

```bash
terraform -chdir=terraform/environments/dev init -backend-config=backend.hcl
```

Expected: `Terraform has been successfully initialized!` A first run also prints `Successfully configured the backend "gcs"!`.

If it fails with `Backend configuration changed`, `backend.hcl` differs from the last `init`; usually it still holds the placeholder. Put the real bucket back and run `init` again.

**Why:** [1.4](notes/info_runbook.md#14-connect-terraform-to-the-state-bucket)

### 1.5 Let Docker push to Artifact Registry

It asks for confirmation; answer `Y`. Then check that the Docker engine answers.

```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
docker info --format '{{.ServerVersion}}'
```

Expected: `Docker configuration file updated.` (or `gcloud credential helpers already registered correctly.`), then a version number. A `500 Internal Server Error` means that Docker Desktop's engine is not running; restart it with `systemctl --user restart docker-desktop`.

**Why:** [1.5](notes/info_runbook.md#15-let-docker-push-to-artifact-registry)

### 1.6 Install the Cloud SQL Auth Proxy

```bash
mkdir -p ~/.local/bin
curl -o ~/.local/bin/cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.28.0/cloud-sql-proxy.linux.amd64
chmod +x ~/.local/bin/cloud-sql-proxy
cloud-sql-proxy --version
```

Expected: `cloud-sql-proxy version 2.28.0+linux.amd64`. If it says `command not found`, log out and in again.

**Why:** [1.6](notes/info_runbook.md#16-install-the-cloud-sql-auth-proxy)

### 1.7 Create the records folder

```bash
mkdir -p .build/real-run/screenshots
git check-ignore .build/real-run
```

Expected: `.build/real-run`, so git will not track it.

<br>

## 2. Deploy

### 2.1 Billing

In the Console, open **Billing → Overview** and check that billing is active and, on a Free Trial, that the credit is still valid. Part A's budget alerts at 50 % and 90 % are expected while Cloud SQL runs.

### 2.2 Image tag

Deploy from `feature/cloud-run-deployment`, up to date and with a clean working tree. Do not commit during the run.

```bash
git pull
git status --short
git rev-parse --short HEAD
```

Expected: `Already up to date.`, then nothing from `git status`, then the short hash. Put the hash into `terraform/environments/dev/terraform.tfvars`, for example `image_tag = "a1b2c3d"`.

**Why:** [2.2](notes/info_runbook.md#22-image-tag)

### 2.3 Plan

```bash
( set -x; terraform -chdir=terraform/environments/dev plan -no-color ) 2>&1 | tee .build/real-run/s2-3-plan.txt
echo "${PIPESTATUS[0]}"
```

Expected: `Plan: 13 to add, 0 to change, 0 to destroy.`, then `0`. Any `destroy` or a different number: stop and check.

**Why:** [2.3](notes/info_runbook.md#23-plan)

### 2.4 Create the registry only

Answer `yes` when the plan shows `1 to add`.

```bash
( set -x; terraform -chdir=terraform/environments/dev apply -no-color -target=module.content_hub.google_artifact_registry_repository.app ) 2>&1 | tee .build/real-run/s2-4-apply-registry.txt
echo "${PIPESTATUS[0]}"
```

Expected: the warnings "Resource targeting is in effect" and "Applied changes may be incomplete", then `Apply complete! Resources: 1 added, 0 changed, 0 destroyed.` and the output `registry_uri`.

**Why:** [2.4](notes/info_runbook.md#24-create-the-registry-only)

### 2.5 Build and push the image

Replace `<image-tag>` with the hash from step 2.2.

```bash
IMAGE="$(terraform -chdir=terraform/environments/dev output -raw registry_uri)/content-hub:<image-tag>"
echo "$IMAGE"
docker build --platform linux/amd64 -t "$IMAGE" .
( set -x; docker push "$IMAGE" ) 2>&1 | tee .build/real-run/s2-5-push.txt
echo "${PIPESTATUS[0]}"
```

Expected: every layer shows `Pushed`, and the last line is `<image-tag>: digest: sha256:... size: ...`. The output shows no progress bars, so a large layer can stay at `Waiting` for a minute.

**It hangs** (no new line for 3 minutes, and `docker info` answers `500`): press Ctrl+C. In Docker Desktop, open **Settings → Docker Engine**, add `"max-concurrent-uploads": 1` to the JSON and click **Apply & restart**. Then push again; layers already uploaded show `Layer already exists`.

**Screenshot:** `s2-5-registry.png`: **Artifact Registry → `content-hub` → `content-hub`**, the digest with the tag.

**Why:** [2.5](notes/info_runbook.md#25-build-and-push-the-image)

### 2.6 Create the rest

**The cost starts here.** Cloud SQL takes about 10 minutes. Answer `yes` when the plan shows `12 to add`.

```bash
( set -x; date -u; terraform -chdir=terraform/environments/dev apply -no-color ) 2>&1 | tee .build/real-run/s2-6-apply.txt
echo "${PIPESTATUS[0]}"
```

Expected: `Apply complete! Resources: 12 added, 0 changed, 0 destroyed.`, then the three outputs: `registry_uri`, `service_url` and `sql_connection_name`.

- **It fails on a permission (`403`):** wait a few minutes, then run the same command again with `tee -a`.
- **It fails on Cloud Run:** do not run it again; read the logs (step 2.9).

**Screenshots:**

| File                    | Console page and what it shows                                                                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `s2-6-sql.png`          | **SQL → the instance:** running, PostgreSQL 18, Enterprise edition, `db-f1-micro`                                                     |
| `s2-6-secret.png`       | **Secret Manager → `content-hub-database-url` → Versions:** one enabled version                                                       |
| `s2-6-iam.png`          | **IAM → View by principals**, filtered to `content-hub-app`: the role **Cloud SQL Client**; the filter hides your email               |
| `s2-6-run.png`          | **Cloud Run → `content-hub` → Networking:** the green tick, the URL, the region and **Ingress: All**; the Logs tab shows earlier runs |
| `s2-6-run-revision.png` | **Revision history → the revision:** max instances, the image, `DATABASE_URL` from the secret, **Cloud SQL Connections** expanded     |
| `s2-6-run-security.png` | **Security** tab: the banner "publicly accessible because 'allUsers' has been granted permission"                                     |

- **Never click View secret value** on the secret's page.
- **Do not click Allow public access or Remove access for allUsers** on the Security tab: either one changes the service outside Terraform.

**Why:** [2.6](notes/info_runbook.md#26-create-the-rest)

### 2.7 No drift

```bash
( set -x; terraform -chdir=terraform/environments/dev plan -no-color ) 2>&1 | tee .build/real-run/s2-7-plan-after-apply.txt
echo "${PIPESTATUS[0]}"
```

Expected: `No changes. Your infrastructure matches the configuration.`

**Why:** [2.7](notes/info_runbook.md#27-no-drift)

### 2.8 The app answers

Until part 3, every `/api` route that reads the database answers `500`; `/docs` does not need the database. The first request can take about 10 seconds (a cold start).

```bash
SERVICE_URL=$(terraform -chdir=terraform/environments/dev output -raw service_url)
echo "$SERVICE_URL"
( set -x; curl -sS -i "$SERVICE_URL/docs" 2>&1 | head -n 12 ) 2>&1 | tee .build/real-run/s2-8-docs.txt
```

Expected: `HTTP/2 200`, `content-type: text/html` and the start of the Swagger UI's HTML.

**Why:** [2.8](notes/info_runbook.md#28-the-app-answers)

### 2.9 The start-up in the logs

Replace `<today>` with the date of the run, for example `2026-11-21`. Cloud Logging keeps the entries of earlier runs, and every run's service has the same name.

```bash
PROJECT_ID=$(terraform -chdir=terraform/environments/dev output -raw sql_connection_name | cut -d: -f1)
echo "$PROJECT_ID"
( set -x; gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="content-hub" AND timestamp>="<today>T00:00:00Z"' \
  --project="$PROJECT_ID" --limit=30 --format='value(timestamp, textPayload)' ) 2>&1 | tee .build/real-run/s2-9-run-logs.txt
```

Expected, newest lines first, all from today: the `GET /docs` request from step 2.8 with `200 OK`, `Application startup complete.`, `Waiting for application startup.` and `Started server process [1]`. Some lines are empty.

**Screenshot:** `s2-9-run-logs.png`: **Cloud Run → Observability → Logs**, today's line `Application startup complete.` The list starts with the entries of earlier runs; scroll down to today's.

**Why:** [2.9](notes/info_runbook.md#29-the-start-up-in-the-logs)

<br>

## 3. Schema and seed

### 3.1 Start the Auth Proxy

In a **second terminal**, in the repository root:

```bash
cloud-sql-proxy --port 5433 "$(terraform -chdir=terraform/environments/dev output -raw sql_connection_name)"
```

Expected: `Listening on 127.0.0.1:5433`, then `The proxy has started successfully and is ready for new connections!` Leave it running.

**Why:** [3.1](notes/info_runbook.md#31-start-the-auth-proxy)

### 3.2 Read the database password

In the **first terminal**. Not recorded: no `set -x` and no `tee`.

```bash
DB_PASSWORD=$(gcloud secrets versions access latest --secret=content-hub-database-url --project="$PROJECT_ID" | sed -E 's|^postgresql://[^:]+:([^@]+)@.*|\1|')
echo ${#DB_PASSWORD}
```

Expected: `32`, the password length. `0` means that `PROJECT_ID` is empty; set it again as in step 2.9.

**Why:** [3.2](notes/info_runbook.md#32-read-the-database-password)

### 3.3 Run the schema, then the seed

With **Docker Desktop**:

```bash
docker run --rm -e PGPASSWORD="$DB_PASSWORD" \
  -v "$PWD/db/init:/init:ro" -v "$PWD/db/seed:/seed:ro" \
  postgres:18.7 psql "host=host.docker.internal port=5433 user=content_hub dbname=content_hub" \
  -v ON_ERROR_STOP=1 -f /init/01-schema.sql -f /init/02-seed.sql 2>&1 | tee .build/real-run/s3-3-seed.txt
echo "${PIPESTATUS[0]}"
```

With **Docker Engine**, use `--network host` and `host=127.0.0.1` instead (not tested).

Expected: 12 `CREATE TABLE` lines, 12 `COPY <n>` lines (190 rows), 7 `setval` results, no `ERROR`, then `0`.

If it stops with an `ERROR`, do not run it again: the tables created before the error already exist.

**Why:** [3.3](notes/info_runbook.md#33-run-the-schema-then-the-seed)

### 3.4 Stop the Auth Proxy and forget the password

1. In the second terminal, press Ctrl+C.
2. In the first terminal:

   ```bash
   unset DB_PASSWORD
   ```

<br>

## 4. Check the app

### 4.1 The API

```bash
( set -x; for path in /api/blog /api/me /api/unknown; do curl -sS -i -w '\n' "$SERVICE_URL$path"; done ) 2>&1 | tee .build/real-run/s4-api-checks.txt
```

| Request        | Expected                                |
| -------------- | --------------------------------------- |
| `/api/blog`    | `200` with the 13 seed posts            |
| `/api/me`      | `401` with `{"detail":"Not signed in"}` |
| `/api/unknown` | `404` with `{"detail":"Not Found"}`     |

**Why:** [4.1](notes/info_runbook.md#41-the-api)

### 4.2 The browser

**Use one address for every check:** `<service-url>` below is the output `service_url`; `echo "$SERVICE_URL"` prints it. Do not use the URL in the Console's page header (`content-hub-<project-number>.europe-west1.run.app`): it reaches the same service, but a login on one address does not count on the other, and it puts the project number into every screenshot.

| Step | Action                                                                             | Expected                                              | Screenshot               |
| ---- | ---------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------ |
| 1    | Open `<service-url>/blog`                                                          | The seed posts, newest first                          | `s4-blog.png`            |
| 2    | Open `<service-url>/blog/1` and press F5                                           | The post, not a `404`                                 | `s4-blog-reload.png`     |
| 3    | Open `<service-url>/docs`                                                          | The Swagger UI                                        | `s4-docs.png`            |
| 4    | **POST /api/mock-login** → **Try it out**, body `{ "person_id": 1 }` → **Execute** | `200` with `{"id": 1, "full_name": "Martha Lindley"}` | `s4-login.png`           |
| 5    | **GET /api/me** → **Try it out** → **Execute**                                     | `200` with the same person                            | `s4-me.png`              |
| 6    | DevTools (F12) → **Application → Storage → Cookies** → the service address         | `session_id` with ✓ **HttpOnly**, ✓ **Secure**, `Lax` | `s4-cookie.png`          |
| 7    | At `<service-url>/blog`, click **Add new post**, fill in the form and save         | The new post at `/blog/14`                            | `s4-post-new.png`        |
| 8    | **Edit** the post, change the title and save                                       | The new title                                         |                          |
| 9    | **Delete** the post and confirm                                                    | Back at `/blog`; the post is gone                     |                          |
| 10   | In `/docs`: **POST /api/mock-logout** → **Execute**                                | `204`                                                 | `s4-logout.png`          |
| 11   | **GET /api/me** → **Execute**                                                      | `401` with `{"detail": "Not signed in"}`              | `s4-me-after-logout.png` |

**Logged out after a pause:** after about 15 minutes without a request, Cloud Run scales to zero and the mock sessions are gone. Log in again (step 4).

**Why:** [4.2](notes/info_runbook.md#42-the-browser)

<br>

## 5. Remove everything

### 5.1 Destroy every resource of this app

Answer `yes` when the plan shows `13 to destroy`. Part A stays up.

```bash
( set -x; date -u; terraform -chdir=terraform/environments/dev destroy -no-color ) 2>&1 | tee .build/real-run/s5-1-destroy.txt
echo "${PIPESTATUS[0]}"
```

Expected: `Destroy complete! Resources: 13 destroyed.`

If it fails on one resource, stop and read the error: the remaining resources keep running and costing money.

**Why:** [5.1](notes/info_runbook.md#51-destroy-every-resource-of-this-app)

### 5.2 No instance left

```bash
( set -x; gcloud sql instances list --project="$PROJECT_ID" ) 2>&1 | tee .build/real-run/s5-2-after-destroy.txt
```

Expected: `Listed 0 items.` In a new terminal, set `PROJECT_ID=<project-id>` first; the outputs are gone after `destroy`.

**Screenshot:** `s5-sql-empty.png`: open **SQL** from the main menu, not from an open tab of the deleted instance. It shows the "Get started" page. Do not click **Create free instance**.

- **Never `gcloud projects delete`:** it removes Part A and the pipeline's state with it.
- **The next run:** gets a new instance name and needs part 3 again.

**Why:** [5.2](notes/info_runbook.md#52-no-instance-left)
