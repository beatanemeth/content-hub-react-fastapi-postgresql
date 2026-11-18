# Runbook: deploy to GCP and remove it again

> **Not run yet:** written in Phase 6 of [evolution_roadmap_deployment.md](claude/evolution_roadmap_deployment.md). The commands change a real GCP project and cost money; the maintainer runs them by hand.

Every command runs in the **repository root**. `terraform -chdir=terraform/environments/dev` runs Terraform in the environment folder without leaving the root. Replace `<project-id>` with the real project ID.

| Part                                               | When                            | Cost                                  |
| -------------------------------------------------- | ------------------------------- | ------------------------------------- |
| [Records of the run](#records-of-the-run)          | Every run                       | None                                  |
| [1. Before the first run](#1-before-the-first-run) | Once per laptop and project     | None                                  |
| [2. Deploy](#2-deploy)                             | Every run                       | Cloud SQL is charged from step 2.6 on |
| [3. Schema and seed](#3-schema-and-seed)           | Every run, after a new instance | Included in the Cloud SQL cost        |
| [4. Check the app](#4-check-the-app)               | Every run                       | Cloud Run stays in the free tier      |
| [5. Remove everything](#5-remove-everything)       | At the end of every run         | Stops the cost                        |

<br>

## Records of the run

Two kinds of record prove the deployment together: **terminal output** saved as text files, and **Console screenshots**. Their times and names should match each other.

- **Save first to `.build/real-run/`:** the folder is git-ignored, so nothing is published by accident. After the run, review each file; only cleaned copies go to `docs/real-run/` (text, with a README table: file, what it shows, command) and `docs/assets/real-run/` (screenshots).
- **`2>&1 | tee <file>`:** the output still shows on screen and is also written to the file; the `yes` prompt of `apply` and `destroy` still works. `tee -a` appends, for example a second `apply` after a failed one. `-no-color` keeps colour codes out of Terraform's files.
- **Did the command succeed?** With `| tee`, the shell reports the result of `tee`, not of the command. Run `echo "${PIPESTATUS[0]}"` right after: `0` means success.
- **Hide before publishing:** the project ID, the project number, your email and the billing account ID. In text files, replace them with `<project-id>`, `<project-number>`, `<email>` and `<billing-account-id>`; in screenshots, blur them. Part A's project stays up after the run, so its ID stays private too.
- **Never record the password:** step 3.2 is not captured, and no screenshot shows the secret's value.

**Screenshots**, saved to `.build/real-run/screenshots/` under these names:

| File                    | When               | Console page and what it shows                                                              |
| ----------------------- | ------------------ | ------------------------------------------------------------------------------------------- |
| `s2-1-billing.png`      | Step 2.1           | **Billing → Overview:** the Free Trial credit and its end date                              |
| `s2-5-registry.png`     | After step 2.5     | **Artifact Registry → `content-hub`:** the image `content-hub` with the tag from step 2.2   |
| `s2-6-sql.png`          | After step 2.6     | **SQL → the instance:** running, PostgreSQL 18, Enterprise edition, `db-f1-micro`           |
| `s2-6-secret.png`       | After step 2.6     | **Secret Manager → `content-hub-database-url`:** one enabled version (never the value)      |
| `s2-6-iam.png`          | After step 2.6     | **IAM:** `content-hub-app` with **Cloud SQL Client**                                        |
| `s2-6-run.png`          | After step 2.6     | **Cloud Run → `content-hub`:** the healthy revision                                         |
| `s2-6-run-revision.png` | After step 2.6     | The revision's details: the image, `DATABASE_URL` from the secret, the Cloud SQL connection |
| `s2-6-run-security.png` | After step 2.6     | **Security** tab: public access (no authentication)                                         |
| `s2-8-run-logs.png`     | After step 2.8     | **Cloud Run → Logs:** `Application startup complete`                                        |
| `s4-blog.png`           | Part 4             | The browser at `<service-url>/blog`: the seed posts                                         |
| `s4-cookie.png`         | Part 4             | DevTools → **Application → Cookies:** the session cookie marked **Secure**                  |
| `s5-billing-report.png` | A day after part 5 | **Billing → Reports**, filtered to the project: the real cost of the run                    |
| `s5-sql-empty.png`      | After step 5.2     | **SQL:** no instance left                                                                   |

<br>

## 1. Before the first run

Skip a step that is already done; each one is safe to run again.

1. **Log in twice:** the first login is for `gcloud`, the second for Terraform and the Auth Proxy (Application Default Credentials).

   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Part A request:** turn on the two APIs that Part A's `bootstrap.sh` does not enable. Done on 2026-11-18. Part A already enables `run`, `artifactregistry` and `iam`.

   ```bash
   gcloud services enable sqladmin.googleapis.com secretmanager.googleapis.com --project=<project-id>
   ```

3. **Local values:** copy the two `.example` files and replace the placeholders. Both copies are git-ignored.

   ```bash
   cp terraform/environments/dev/terraform.tfvars.example terraform/environments/dev/terraform.tfvars
   cp terraform/environments/dev/backend.hcl.example terraform/environments/dev/backend.hcl
   ```

   | File               | Holds                                                    | Read by                      |
   | ------------------ | -------------------------------------------------------- | ---------------------------- |
   | `terraform.tfvars` | `project_id`, and `image_tag` (set in step 2.2)          | `terraform plan` and `apply` |
   | `backend.hcl`      | `bucket = "<project-id>-tfstate"`, Part A's state bucket | `terraform init`             |

4. **Connect Terraform to the state bucket:**

   ```bash
   terraform -chdir=terraform/environments/dev init -backend-config=backend.hcl
   ```

   Expected: `Successfully configured the backend "gcs"!`

5. **Let Docker push to Artifact Registry:** this adds `gcloud` as the login helper for the registry host in `~/.docker/config.json`.

   ```bash
   gcloud auth configure-docker europe-west1-docker.pkg.dev
   ```

6. **Install the Cloud SQL Auth Proxy** (v2.28.0, Linux 64-bit) in `~/.local/bin`, outside the repository.

   ```bash
   mkdir -p ~/.local/bin
   curl -o ~/.local/bin/cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.28.0/cloud-sql-proxy.linux.amd64
   chmod +x ~/.local/bin/cloud-sql-proxy
   ```

   Expected: `cloud-sql-proxy --version` prints `2.28.0`. If it says `command not found`, log out and in again: Ubuntu's `~/.profile` adds `~/.local/bin` to the `PATH` at login, but only when the folder already exists.

7. **Create the records folder** (git-ignored):

   ```bash
   mkdir -p .build/real-run/screenshots
   git check-ignore .build/real-run
   ```

   Expected: `git check-ignore` prints `.build/real-run`, so git will not track it.

<br>

## 2. Deploy

1. **Free Trial:** in the Console, open **Billing** and check that the credit is still valid and has not ended. Part A's budget alerts at 50 % and 90 % are expected while Cloud SQL runs; the budget never stops spending.

2. **Image tag:** check out the commit to deploy (normally `feature/gcp-deployment`, with a clean working tree), then print its short hash:

   ```bash
   git status --short
   git rev-parse --short HEAD
   ```

   Expected: `git status` prints nothing. Put the hash into `terraform/environments/dev/terraform.tfvars`, for example `image_tag = "ff0e351"`.

3. **Plan:**

   ```bash
   terraform -chdir=terraform/environments/dev plan -no-color 2>&1 | tee .build/real-run/s2-3-plan.txt
   ```

   Expected: `Plan: 13 to add, 0 to change, 0 to destroy.`

4. **Create the registry only:** Cloud Run starts the image during `apply`, so the image must be in the registry first. `-target` limits this `apply` to one resource.

   ```bash
   terraform -chdir=terraform/environments/dev apply -no-color -target=module.content_hub.google_artifact_registry_repository.app 2>&1 | tee .build/real-run/s2-4-apply-registry.txt
   ```

   Expected: a warning that resource targeting is in effect, then `Apply complete! Resources: 1 added, 0 changed, 0 destroyed.`

5. **Build and push the image:** the image name is the registry address, the image name `content-hub` and the tag from step 2.2.

   ```bash
   IMAGE=europe-west1-docker.pkg.dev/<project-id>/content-hub/content-hub:<image-tag>
   docker build --platform linux/amd64 -t "$IMAGE" .
   docker push "$IMAGE" 2>&1 | tee .build/real-run/s2-5-push.txt
   ```

   Expected: the push ends with a line that holds `digest: sha256:...`. The build output is long and proves nothing the push does not, so it is not saved.

6. **Create the rest:** Cloud SQL takes about 10 to 15 minutes. The cost starts here. `date -u` writes the UTC start time as the first line, to match the screenshots.

   ```bash
   { date -u; terraform -chdir=terraform/environments/dev apply -no-color; } 2>&1 | tee .build/real-run/s2-6-apply.txt
   ```

   Expected: `Apply complete! Resources: 12 added, 0 changed, 0 destroyed.`, then the four outputs: `registry_uri`, `service_account_email`, `service_url` and `sql_connection_name`. If it fails on a permission, wait a few minutes and run it again with `tee -a`.

7. **No drift:**

   ```bash
   terraform -chdir=terraform/environments/dev plan -no-color 2>&1 | tee .build/real-run/s2-7-plan-after-apply.txt
   ```

   Expected: `No changes. Your infrastructure matches the configuration.`

8. **The app started:** the lifespan opens the connection pool before the first request, so a running service has already reached Cloud SQL. The tables do not exist yet: until part 3, every `/api` route that reads the database answers `500`.

   ```bash
   SERVICE_URL=$(terraform -chdir=terraform/environments/dev output -raw service_url)
   curl -sS -i "$SERVICE_URL/docs" 2>&1 | head -n 12 | tee .build/real-run/s2-8-docs.txt
   ```

   Expected: `HTTP/2 200` and the start of the Swagger UI's HTML. The home page opens in the browser at the same address.

9. **The start-up in the logs:**

   ```bash
   gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="content-hub"' \
     --project=<project-id> --limit=30 --format='value(timestamp, textPayload)' 2>&1 | tee .build/real-run/s2-9-run-logs.txt
   ```

   Expected: a line with `Application startup complete.`, newest lines first.

<br>

## 3. Schema and seed

The schema and the seed run with psql in a `postgres:18.7` container, so the laptop needs no psql of the right version. The Auth Proxy opens a local port that leads to Cloud SQL through Google's tunnel.

1. **Start the Auth Proxy**, in a second terminal (also in the repository root). Port `5433`, because the Compose database uses `5432`.

   ```bash
   cloud-sql-proxy --port 5433 "$(terraform -chdir=terraform/environments/dev output -raw sql_connection_name)"
   ```

   Expected: `The proxy has started successfully and is ready for new connections!` Leave it running.

2. **Read the database password** from the secret, in the first terminal. The password is the part of `DATABASE_URL` between `content_hub:` and `@`.

   ```bash
   DB_PASSWORD=$(gcloud secrets versions access latest --secret=content-hub-database-url --project=<project-id> | sed -E 's|^postgresql://[^:]+:([^@]+)@.*|\1|')
   ```

   Expected: no output. `echo ${#DB_PASSWORD}` prints `32`, the password length, without showing the password.

3. **Run the schema, then the seed:** `--network host` lets the container reach the proxy on `127.0.0.1:5433`. `db/seed` is mounted on `/seed`, the path that `\copy` reads in `02-seed.sql`.

   ```bash
   docker run --rm --network host -e PGPASSWORD="$DB_PASSWORD" \
     -v "$PWD/db/init:/init:ro" -v "$PWD/db/seed:/seed:ro" \
     postgres:18.7 psql "host=127.0.0.1 port=5433 user=content_hub dbname=content_hub" \
     -v ON_ERROR_STOP=1 -f /init/01-schema.sql -f /init/02-seed.sql 2>&1 | tee .build/real-run/s3-3-seed.txt
   ```

   Expected: `CREATE TABLE` lines, then 12 `COPY <n>` lines (for example `COPY 13` for `post`), then the `setval` results. No `ERROR`: `ON_ERROR_STOP=1` stops at the first one.

4. **Stop the Auth Proxy:** press Ctrl+C in the second terminal.

<br>

## 4. Check the app

`SERVICE_URL` is set in step 2.8. The three `curl` checks run in one loop and are saved together:

```bash
for path in /api/blog /api/me /api/unknown; do echo "== GET $path"; curl -sS -i "$SERVICE_URL$path"; echo; done 2>&1 | tee .build/real-run/s4-api-checks.txt
```

| Check                                                                                        | Expected                                           | Shows                                                 |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------- | ----------------------------------------------------- |
| `curl -i "$SERVICE_URL/api/blog"`                                                            | `200` with the seed posts                          | The app reads the seeded database through the socket. |
| `curl -i "$SERVICE_URL/api/me"`                                                              | `401` with `{"detail":"Not signed in"}`            | Without a cookie, the app knows no one.               |
| `curl -i "$SERVICE_URL/api/unknown"`                                                         | `404` with `{"detail":"Not Found"}`                | Unknown API paths get JSON, not the React page.       |
| Browser: reload `<service-url>/blog/1`                                                       | The post, not a `404`                              | The fallback to `index.html` works on Cloud Run.      |
| Browser: **POST /api/mock-login** in `<service-url>/docs`, `{ "person_id": 1 }`              | `200`; the cookie is marked **Secure** in DevTools | The secure cookie works over HTTPS.                   |
| Browser: add, edit and delete a post at `<service-url>/blog`, then **POST /api/mock-logout** | Each works; then `204`                             | Writing works end to end.                             |

- **Logged out after a pause:** Cloud Run stops the only instance when no request comes for a while, and the mock sessions live in that instance's memory. A new deployment (a new revision) has the same effect. Log in again.
- **The first `apply` fails on a permission:** a new grant can take a minute to reach every Google service. Run the same `apply` again after a few minutes.

<br>

## 5. Remove everything

1. **Destroy every resource of this app:** Part A (the project, the budget, the state bucket, the enabled APIs) stays up.

   ```bash
   { date -u; terraform -chdir=terraform/environments/dev destroy -no-color; } 2>&1 | tee .build/real-run/s5-1-destroy.txt
   ```

   Expected: `Destroy complete! Resources: 13 destroyed.` The database user is only removed from the state (`deletion_policy = "ABANDON"`); deleting the instance removes it in Cloud SQL.

2. **No instance left:**

   ```bash
   gcloud sql instances list --project=<project-id> 2>&1 | tee .build/real-run/s5-2-after-destroy.txt
   ```

   Expected: `Listed 0 items.`

- **Never `gcloud projects delete`:** it removes Part A and the pipeline's state with it.
- **The next run gets a new instance name:** Cloud SQL blocks a deleted name for up to a week, so `random_id` gives the next instance a new suffix.
- **Seed again after every new instance:** a new instance is empty; run part 3 again.
