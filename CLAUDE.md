# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. General working rules live in `.claude/rules/`.

<br>

## Project context

- **Purpose:** a learning project to practise **FastAPI**, **Python**, **Docker**, **PostgreSQL** and REST API design; later **Terraform** and **GCP**.

<br>

## Repository layout

| Path                  | Holds                                                                     |
| --------------------- | ------------------------------------------------------------------------- |
| `app/`                | The FastAPI backend; `main.py` creates the app, `db.py` holds the pool    |
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

<br>

## Code checks

Run in the project root. The settings are in `pyproject.toml`.

```bash
uv run ruff check            # lint rules
uv run ruff format --check   # formatting, without changing files
uv run pyright               # type checks
```
