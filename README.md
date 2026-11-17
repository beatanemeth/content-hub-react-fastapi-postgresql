# Content hub: a JSON REST API with FastAPI and PostgreSQL

A learning project to practise **FastAPI**, **Python**, **PostgreSQL** and REST API design by building a small JSON REST API for blog posts. The posts are stored in PostgreSQL, which runs in a Docker container.

> The API rebuilds the Express API of [content-hub-react-express-postgresql](https://github.com/beatanemeth/content-hub-react-express-postgresql) in FastAPI. The **React** frontend comes from the same repository, and its pages are adapted to the FastAPI API step by step.

> The full build log, step by step, is in [NOTES.md](NOTES.md).

> The app has no sign-in or sign-up and only the blog post endpoints. The workaround for the missing parts, and the reasons for it, are in [info_out_of_scope_workaround.md](docs/notes/info_out_of_scope_workaround.md).

> **Authorship note:** Planned by me, implemented with Claude Code. Content by me, wording by Claude.

<br>

## Technical details

| Item             | Version         |
| ---------------- | --------------- |
| Operating system | Linux Mint 21.2 |
| uv               | 0.13.7          |
| Python           | 3.14.10         |
| FastAPI          | 0.163.1         |
| PostgreSQL       | 18              |
| asyncpg          | 0.32.0          |
| Ruff             | 0.17.5          |
| Pyright          | 1.1.414         |
| Node.js          | 24.14.0         |
| React            | 19.3.1          |
| React Router     | 8.5.1           |
| Vite             | 8.3.8           |
| Tailwind CSS     | 4.3.5           |

<br>

## Run the API

In the project root:

```bash
cp .env.example .env             # then set real values in .env
docker compose up -d             # starts PostgreSQL and loads the seed data
```

In `backend/`:

```bash
uv sync                          # installs the dependencies into backend/.venv/
uv run fastapi dev app/main.py   # starts the server on port 8000
```

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **Requests:** `blog.http` holds a request for each endpoint; run it from top to bottom with the VS Code REST Client extension.
- **Reset the data:** the posts stay in the `pgdata` volume across restarts. `docker compose down -v`, then `docker compose up -d`, starts again from the seed data.

<br>

## Run the frontend

In `frontend/`, with the API running:

```bash
npm install   # installs the dependencies into node_modules/
npm run dev   # starts the Vite dev server on port 5173
```

- **App:** `http://localhost:5173`
- **Node.js version:** Volta reads `volta.node` in `package.json` and switches to Node.js 24.14.0 inside `frontend/`.
- **API calls:** the Vite dev server forwards every `/api` request to `http://localhost:8000`.
