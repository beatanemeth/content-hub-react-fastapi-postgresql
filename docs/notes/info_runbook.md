# Runbook explained: the reasons behind each step

> The reasons and the findings of the real run for [runbook.md](../runbook.md). The headings use the runbook's step numbers; steps that need no explanation are left out. The records of the real run are in [real-run/](../real-run/README.md).

<br>

## Google Cloud services used in this project

| Service               | Created by               | Used for                                                                                               |
| --------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------ |
| **Cloud Billing**     | Part A                   | The Free Trial credit and the budget alerts at 50 % and 90 %                                           |
| **Cloud Storage**     | Part A                   | The state bucket `<project-id>-tfstate`; this app's state is under the prefix `content-hub`            |
| **IAM**               | This app (`iam.tf`)      | The service account `content-hub-app`, with the **Cloud SQL Client** role and access to the one secret |
| **Artifact Registry** | This app (`registry.tf`) | The Docker repository `content-hub`, which stores the image you push in step 2.5                       |
| **Cloud SQL**         | This app (`sql.tf`)      | The PostgreSQL 18 instance, the database `content_hub` and its user                                    |
| **Secret Manager**    | This app (`secrets.tf`)  | The secret `content-hub-database-url`, which holds `DATABASE_URL` with the generated password          |
| **Cloud Run**         | This app (`run.tf`)      | Runs the container; the URL is public, so anyone can open it without a Google login                    |
| **Cloud Logging**     | Automatic                | Collects what the container prints, such as `Application startup complete` (step 2.9)                  |

The Cloud SQL Auth Proxy is not a service. It is a program on your laptop (see step 1.6).

<br>

## How to run the commands

Every command works from the repository root for these reasons:

- **`-chdir` moves Terraform, not the shell:** Terraform switches into `terraform/environments/dev` before it does anything. So it finds `main.tf`, `terraform.tfvars`, `backend.hcl` and `.terraform/` there, as if you had run `cd` first.
- **The rest stays in the root:** the shell is still in the root, so `| tee .build/real-run/...` writes to the root's `.build/`. `docker build ... .` also uses the root as the build context, and `-v "$PWD/db/init:..."` uses the root's `db/`.
- **The benefit:** you never need `cd`, and every path in the runbook is relative to one folder.

The Terraform outputs are gone after `destroy`. So step 5.2 uses `PROJECT_ID` from step 2.9, or `PROJECT_ID=<project-id>` in a new terminal.

<br>

## Records of the run

Two kinds of record prove the deployment together: **terminal output** saved as text files, and **Console screenshots**. Their times and names should match each other.

- **Save first to `.build/real-run/`:** the folder is git-ignored, so nothing is published by accident. After the run, review each file; only cleaned copies go to `docs/real-run/` (text, with a README table: file, what it shows, command) and `docs/real-run/real-run/` (screenshots).
- **`2>&1 | tee <file>`:** the output still shows on screen and is also written to the file; the `yes` prompt of `apply` and `destroy` still works. `tee -a` appends, for example a second `apply` after a failed one. `-no-color` keeps colour codes out of Terraform's files.
- **`( set -x; ... )`:** the shell writes each command, with a `+` in front, before it runs it, so the file holds the command as well as its output. The parentheses start a subshell, so `set -x` stays off in your terminal. Variables appear with their real values, such as the project ID, so hide them like the output. Part 3 never uses it, because it would write the database password into the file.
- **Did the command succeed?** With `| tee`, the shell reports the result of `tee`, not of the command. `echo "${PIPESTATUS[0]}"` right after prints the command's own result: `0` means success.
- **Hide before publishing:** the project ID, the project number, your email, the billing account ID and the service URL. In text files, replace them with `<project-id>`, `<project-number>`, `<email>`, `<billing-account-id>` and `<service-url>`; in screenshots, cover them. Part A's project stays up after the run, so its ID stays private too.
- **Screenshot names:** a Linux screenshot is saved as `Screenshot from <date> <time>.png`; rename it right after the check, to the name the runbook gives.

<br>

## 1. Before the first run

### 1.1 Log in twice

The first login is for `gcloud`, the second for Terraform and the Auth Proxy (Application Default Credentials). Both logins are saved in `~/.config/gcloud/` and are not tied to one project, so logins from an earlier project still work.

### 1.2 Part A request: two more APIs

Part A's `bootstrap.sh` enables `run`, `artifactregistry` and `iam`, but not these two:

- **Cloud SQL Admin API** (`sqladmin`): Terraform uses it to create and delete the instance. The Auth Proxy also uses it to look up the instance and get a certificate for the connection.
- **Secret Manager API** (`secretmanager`): it stores the secret that holds `DATABASE_URL`.

Part A comes from the earlier pipeline project: [`scripts/bootstrap.sh`](../../../gcp-content-intelligence-platform_implementation/scripts/bootstrap.sh) created the project, the billing link, the budget and the state bucket.

### 1.4 Connect Terraform to the state bucket

The command does two things:

- **Downloads the providers** (`google` and `random`) into `terraform/environments/dev/.terraform/`. In the real run: `google` v8.12.0 and `random` v3.9.1.
- **Connects to the state bucket:** after this, Terraform reads and writes its state in `gs://<project-id>-tfstate/content-hub/`, not in a local file.

Running it again is safe: it reuses the providers and the backend settings.

### 1.5 Let Docker push to Artifact Registry

The command adds `gcloud` as the login helper for the registry host in `~/.docker/config.json`. Then `docker push` gets its login from your `gcloud` account and needs no password. The file now holds:

```json
"credHelpers": {
  "europe-west1-docker.pkg.dev": "gcloud"
}
```

### 1.6 Install the Cloud SQL Auth Proxy

The proxy is used only in part 3, to create the tables and load the seed data from your laptop.

- **Why you need it:** the Cloud SQL instance has a public IP address, but no address is on its allow list. So `psql` cannot connect to it directly.
- **How it connects:** the proxy logs in with your Google account (Application Default Credentials, from step 1.1) and opens an encrypted tunnel to the instance.
- **What `psql` sees:** a normal local database on port `5433`.

Cloud Run reaches the database in the same way, through a built-in connector. That is why the app's service account needs the **Cloud SQL Client** role.

**`command not found`:** Ubuntu's `~/.profile` adds `~/.local/bin` to the `PATH` at login, but only when the folder already exists. So a new folder needs a new login.

<br>

## 2. Deploy

### 2.1 Free Trial

The budget alerts are only emails; the budget never stops spending.

### 2.2 Image tag

The hash is not an image hash. It is the short hash of the **Git commit**, used as the image's **tag** (its version label).

- **Why a commit hash:** the image is built from the files on disk. If the tag is the commit hash, you can always tell which code an image runs, for example `content-hub:0fa76da` is commit `0fa76da`.
- **Why a clean working tree:** a modified file in `backend/` or `frontend/` would go into the image, but the commit hash would not show that change. Then the tag would point to the wrong code.
- **Why it goes into `terraform.tfvars`:** you use the same tag twice. In step 2.5 Docker pushes `content-hub:<tag>`, and in step 2.6 Terraform tells Cloud Run to run `content-hub:<tag>`. If the two tags are different, Cloud Run cannot find the image.
- **An untracked file is harmless:** in the real run, `git status --short` printed one untracked file in `docs/`. `.dockerignore` lets in only `backend/` and `frontend/`, so `docs/` never reaches the image.
- **Take the hash last:** every new commit changes `HEAD`. So run `git rev-parse --short HEAD` after your last commit, just before the build.

### 2.3 Plan

`plan` is a dry run before `apply`.

- **What it does:** it compares the `.tf` files with the state and with what exists in GCP. Then it lists what `apply` would create, change or delete. It changes nothing and costs nothing.
- **Errors it catches early:** a missing `image_tag`, a wrong project ID or a missing permission. You see them before any resource costs money.
- **The image shows `(known after apply)`:** the image address is built from the registry, which does not exist yet.

`apply` shows the same plan again and waits for `yes`. The saved file records what you approved.

### 2.4 Create the registry only

Cloud Run starts the image during `apply`, so the image must be in the registry first. `-target` limits this `apply` to one resource. Both warnings are normal with `-target`; steps 2.6 and 2.7 cover the rest.

### 2.5 Build and push the image

- **The image name:** the registry address (the output `registry_uri`), the image name `content-hub` and the tag from step 2.2. Reading the address from the output avoids a mistyped project ID.
- **The build output is not saved:** it is long and proves nothing the push does not.
- **The push file is long:** Docker prints many `Waiting` lines; they can be removed from the published copy.
- **Two digests on the image page:** the tagged one is an **index**, a small list that points to the image for each platform. The other one is the `linux/amd64` image itself (78.6 MB in the real run). Cloud Run follows the tag to the index, then to the image.
- **`gcf-artifacts` in the repository list:** Cloud Functions created it for Part B of the pipeline project; this app's Terraform never touches it.

### 2.6 Create the rest

- **The duration:** Cloud SQL took 9 min 13 s in the real run. `date -u` writes the UTC start time at the top of the file, to match the screenshots.
- **A finished `apply`:** Terraform waits until the Cloud Run revision is ready. So a finished `apply` means that the app has already started and reached the database.
- **A failed `apply` on a permission:** a new grant can take a few minutes to reach every Google service.
- **The IAM page shows only Cloud SQL Client:** the second role, **Secret Manager Secret Accessor**, is granted on the one secret, not on the project. The secret's **Permissions** tab shows it.
- **The revision panel does not fit on one screen:** so there are two screenshots, `-a` with the image and `DATABASE_URL`, and `-b` with **Cloud SQL Connections** expanded. The image name is cut off before the tag; `s2-6-apply.txt` records the full name.

The **Security** tab shows **Require authentication**, although the service is public. Cloud Run has two ways to make a service public:

- **IAM stays on, and `allUsers` gets `run.invoker`:** this is what `run.tf` does. The Console marks **Require authentication** and shows the banner "This service is publicly accessible because 'allUsers' has been granted permission on the service."
- **Allow public access:** the newer Console option turns the IAM check off completely.

Both make the URL public. The two buttons on the Security tab change the service outside Terraform, so step 2.7 would show drift.

### 2.7 No drift

This step checks that the `apply` finished cleanly. A second `plan` after `apply` should find nothing left to do.

- **`No changes`:** every resource in GCP matches the `.tf` files.
- **A change listed:** often GCP has filled in a default value that the `.tf` file sets differently. Then every `apply` would try to change that resource again. This is called **drift**, and the `.tf` file needs a fix.

The saved file proves that the deployment matched the code.

### 2.8 The app answers

- **Why `/docs`:** the lifespan opens the connection pool before the first request, so a running service has already reached Cloud SQL. But the tables do not exist until part 3, so the `/api` routes that read the database answer `500`. FastAPI serves `/docs` without the database.
- **`server: Google Frontend`:** the request went through Google's front end over HTTPS.
- **The cold start:** if no request came for about 15 minutes, Cloud Run has stopped the instance (scale to zero) and starts a new one first.

### 2.9 The start-up in the logs

This step checks the start-up from **inside** Cloud Run. Step 2.8 checked it from outside, with `curl`.

`PROJECT_ID` is read from the output `sql_connection_name`, which starts with the project ID (`<project-id>:europe-west1:...`). Steps 3.2 and 5.2 use it again.

`Application startup complete.` is printed by Uvicorn, the server that runs FastAPI, when the lifespan has finished. The lifespan is where the connection pool to Cloud SQL opens. So this line proves three things:

- the container started;
- it read `DATABASE_URL` from the secret;
- it reached the database through the socket.

If the app fails to start, the error (for example, a wrong password or a missing permission) appears here and not in `curl`. The empty log lines are entries without plain text.

The logs of the real run show the instance's life cycle:

| UTC         | Event                                                                       |
| ----------- | --------------------------------------------------------------------------- |
| 13:47:14–15 | First start, during the `apply`; the start-up probe on port 8080 passed     |
| 14:02:17    | Shutdown after 15 minutes without a request (scale to zero)                 |
| 14:17:01–10 | Cold start for the `curl` of step 2.8 (`Reason: AUTOSCALING`), 9.186 s long |
| 14:17:10    | `GET /docs` → `200 OK`                                                      |

<br>

## 3. Schema and seed

The schema and the seed run with `psql` in a `postgres:18.7` container, so the laptop needs no `psql` of the right version. The Auth Proxy opens a local port that leads to Cloud SQL through Google's tunnel.

### 3.1 Start the Auth Proxy

- **Port `5433`:** the Compose database uses `5432`.
- **Not in the codebase:** the proxy is Google's official program, downloaded in step 1.6 into `~/.local/bin/cloud-sql-proxy`, outside the repository, like `gcloud` or `terraform`.

### 3.2 Read the database password

The password is the part of `DATABASE_URL` between `content_hub:` and `@`:

```text
postgresql://content_hub:<password>@/content_hub?host=/cloudsql/<connection-name>
```

The step is not recorded, so the password never reaches a file. `echo ${#DB_PASSWORD}` prints only the length.

### 3.3 Run the schema, then the seed

- **The mounts:** `db/seed` is mounted on `/seed`, the path that `\copy` reads in `02-seed.sql`.
- **`ON_ERROR_STOP=1`:** stops at the first error. A second run after an error fails on `already exists`.
- **The expected numbers:** 12 tables, 190 rows (for example `COPY 13` for `post`) and 7 sequences. The proxy's terminal prints `Accepted connection from 127.0.0.1:...`.

**Docker Desktop and Docker Engine:** the real run used Docker Desktop (context `desktop-linux`). Its first try, with `--network host` and `host=127.0.0.1`, failed with `Connection refused`, although the proxy was running. Docker Desktop runs containers inside a small virtual machine, so `--network host` gives the container the network of that machine, not of the laptop. Nothing listens on `127.0.0.1:5433` inside it. `host.docker.internal` is Docker Desktop's name for the laptop, so the container reaches the proxy through it. With Docker Engine, `--network host` really is the laptop's network.

<br>

## 4. Check the app

### 4.1 The API

| Request        | Shows                                                 |
| -------------- | ----------------------------------------------------- |
| `/api/blog`    | The app reads the seeded database through the socket. |
| `/api/me`      | Without a cookie, the app knows no one.               |
| `/api/unknown` | Unknown API paths get JSON, not the React page.       |

- **`-w '\n'`:** ends each response with a new line. The real run used `curl -sS -i "$SERVICE_URL$path"; echo` instead. The response bodies end without a new line, so each `+ echo` trace line stuck to the end of the JSON.
- **`www-authenticate: APIKey`:** the `401` carries this header from FastAPI's cookie security scheme (`APIKeyCookie`).

### 4.2 The browser

**One address:** the URL is the Terraform output `service_url`. There are three ways to find it:

- **In the first terminal:** `echo "$SERVICE_URL"`, because step 2.8 set this variable.
- **In any terminal, in the root:** `terraform -chdir=terraform/environments/dev output -raw service_url`.
- **In the Console:** **Cloud Run → `content-hub`**; the URL is at the top of the page. This is a second format, with the project number.

A cookie belongs to one host, so a login on one URL does not count on the other. Some URL formats contain the project number, so hide the URL in the records too.

| Check                      | Shows                                                         |
| -------------------------- | ------------------------------------------------------------- |
| Reload of `/blog/1`        | The fallback to `index.html` works on Cloud Run.              |
| `GET /api/me` → `200`      | The browser sent the cookie back, and the app recognised you. |
| The cookie in DevTools     | The secure cookie works over HTTPS.                           |
| The new post at `/blog/14` | The `setval` of the seed worked: the next id after 13.        |
| Logout → `204`             | Writing and signing out work end to end.                      |

- **The login response shows no `set-cookie` header:** browsers hide that header from page JavaScript, including Swagger UI. DevTools shows the cookie.
- **Logged out after a pause:** Cloud Run stops the only instance when no request comes for about 15 minutes, and the mock sessions live in that instance's memory. A new deployment (a new revision) has the same effect.

<br>

## 5. Remove everything

### 5.1 Destroy every resource of this app

- **The order:** Cloud Run goes first; the instance goes last (1 min 52 s in the real run).
- **The database user:** it is only removed from the state (`deletion_policy = "ABANDON"`); deleting the instance removes it in Cloud SQL.

`destroy` leaves Part A untouched. It deletes only the resources listed in this app's state, which is under the prefix `content-hub` in the bucket. That is the 13 resources from `terraform/modules/content_hub/`.

Part A was created by `bootstrap.sh` with `gcloud`, not by Terraform, so this state does not know about it. These all stay:

- the project and its budget;
- the state bucket, which keeps this app's state file, now empty;
- the enabled APIs, including the two from step 1.2. The module has no `google_project_service` resource, so `destroy` cannot turn them off.

### 5.2 No instance left

- **The "Get started" page:** with no instance, Cloud SQL shows it instead of the instance list. **Create free instance** on it starts a new trial instance in this project.
- **`gcloud projects delete`:** it would remove Part A and the pipeline's state with it.
- **The next run gets a new instance name:** Cloud SQL blocks a deleted name for up to a week, so `random_id` gives the next instance a new suffix.
- **Seed again after every new instance:** a new instance is empty.
