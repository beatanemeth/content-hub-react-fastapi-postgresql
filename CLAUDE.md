# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. General working rules live in `.claude/rules/`.

<br>

## Project context

- **Purpose:** a learning project to practise **FastAPI**, **Python**, **Docker**, **PostgreSQL**, REST API design, **Terraform** and **GCP**.
- **Current work:** the local app is finished (tag `v0.3.0`). The deployment to GCP with Terraform follows [evolution_roadmap_deployment.md](docs/claude/evolution_roadmap_deployment.md) on the integration branch `feature/cloud-run-deployment`. The rules for Docker, Terraform and GCP are in [engineer_cloud.md](.claude/rules/engineer_cloud.md).
- **First iteration:** an earlier deployment ran once on GCP from `feature/gcp-deployment` and was destroyed. That branch is a record only; never build on it.

<br>

## Repository layout

| Path                  | Holds                                                                     |
| --------------------- | ------------------------------------------------------------------------- |
| `backend/`            | The FastAPI backend (`app/`), `pyproject.toml` and `uv.lock`              |
| `frontend/`           | The React client (Vite, Tailwind CSS); Node.js is pinned with Volta       |
| `db/`                 | The SQL schema and seed script (`init/`) and the seed CSV files (`seed/`) |
| `docker-compose.yaml` | The PostgreSQL container                                                  |
| `.env.example`        | The variable names for Compose and the app (`DATABASE_URL`)               |
| `blog.http`           | Manual requests for every endpoint (REST Client)                          |
| `docs/`               | The API contract, the roadmaps, and the brand and UI notes                |
| `NOTES.md`            | The build log                                                             |

<br>

## Documentation

- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/latest/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [asyncpg](https://magicstack.github.io/asyncpg/current/)
- [uv](https://docs.astral.sh/uv/)
- [Ruff](https://docs.astral.sh/ruff/)
- [Pyright](https://microsoft.github.io/pyright/)
- [PostgreSQL](https://www.postgresql.org/docs/current/)
- [PostgreSQL Docker image](https://hub.docker.com/_/postgres)
- [React](https://react.dev/reference/react)
- [Vite](https://vite.dev/guide/)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [React Router](https://reactrouter.com/home)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [MDN: HTTP status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [Conventional Commits](https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13)
- [Conventional Branch](https://conventionalbranch.org/)
- [NumPy Style](https://numpydoc.readthedocs.io/en/latest/format.html)
- [JSDoc](https://jsdoc.app/)

### Deployment

- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Terraform](https://developer.hashicorp.com/terraform/docs)
- [Terraform Google provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Artifact Registry](https://cloud.google.com/artifact-registry/docs)
- [IAM](https://cloud.google.com/iam/docs)
- [gcloud CLI reference](https://cloud.google.com/sdk/gcloud/reference)

<br>

## Code checks

Run in `backend/`. The settings are in `pyproject.toml`.

```bash
uv run ruff check            # lint rules
uv run ruff format --check   # formatting, without changing files
uv run pyright               # type checks
```

Run in `frontend/`. The settings are in `eslint.config.js` and `.prettierrc.json`.

```bash
npm run lint                 # lint rules (ESLint)
npm run prettier             # formatting, without changing files
npm run build                # type checks (tsc -b), then the Vite build
```
