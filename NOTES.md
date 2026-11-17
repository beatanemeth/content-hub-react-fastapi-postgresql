# Notes

This file is the build log: the commands, files and checks, in the order the project was built.

<br>

## Goal

The project teaches how a **FastAPI** server is set up by building a small JSON REST API. The data is stored in **PostgreSQL**, and a **React** frontend calls the API.

<br>

## Out of scope

- **Sign-in and sign-up:** there is none; every staff member may create, edit and delete posts.
- **Protected routes:** no page checks who is calling. The write endpoints need the mock session cookie, set by `POST /api/mock-login` in `/docs` or `blog.http`, and answer `401` without it.
- **Detailed input validation:** the browser checks only that each field is filled in (`required`), and the API's Pydantic model checks only that `title`, `summary` and `body` are non-empty strings, that `categories` and `tags` are non-empty lists of labels, and that `published_on` is a real date in the form `YYYY-MM-DD`. Invalid input gets FastAPI's `422`. A post id that is not a whole number from 1 to 2147483647 also gets `422`, before the handler runs. An unknown category or tag label gets `400`. The author is not in the body; it comes from the mock session. The database still enforces its own rules, such as unique labels and foreign keys.
- **Error screens:** the UI shows the API's error message as plain text. There are no error pages, toast messages or retry buttons.
- **Pages beyond the blog:** About, Events, Contact and the footer links show the not-found page.
- **Mobile layout:** the UI is designed for desktop screens only.
- **Automated tests:** the endpoints are checked by hand with `blog.http`.

> The workaround for the out-of-scope parts, and the reasons for it, are in [info_out_of_scope_workaround.md](docs/notes/info_out_of_scope_workaround.md).

<br>

**Build log steps in development order**

## 1. Local Git setup

Run once after cloning, so local merges into `main` create a merge commit (like merging a PR on GitHub) while `git pull` still fast-forwards:

```bash
git config merge.ff false   # merges always create a merge commit
git config pull.ff only     # pulls only fast-forward, with no extra merge commits
git config core.hooksPath .githooks   # merge messages become "chore: merge branch '<name>'"
```

**Notes:**

- **File name:** Git runs a hook only if its file name matches the hook name exactly, with hyphens (`prepare-commit-msg`). Git ignores a file named `prepare_commit_msg` and shows no error.
- **Location:** Git looks for hooks in `.git/hooks/` by default. `core.hooksPath` points it to another folder, here `.githooks/`.
- **Permissions:** the hook file must be executable (`chmod +x`).

<br>

## 2. Add project guide for Claude Code

[CLAUDE.md](CLAUDE.md) gives Claude Code the project context, the repository layout and the docs to read for each layer. The rules in `.claude/rules/` set how Claude works and writes, the `/commit` skill in `.claude/skills/` prepares commits, and `.claude/settings.json` holds the permissions.

<br>

## 3. Set up the Python project and code style

Create `pyproject.toml` and add Ruff (linter and formatter) and Pyright (type checker) as development dependencies:

```bash
uv init --bare              # creates only pyproject.toml
uv add --dev ruff pyright   # adds both tools to the dev group and creates uv.lock
```

The settings live in `pyproject.toml`:

| Section                       | Setting                                    | Purpose                                                                       |
| ----------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------- |
| `[tool.ruff.lint]`            | `select = ["E", "F", "I", "UP", "B", "D"]` | Checks basic errors, import order, modern syntax, common bugs and docstrings. |
| `[tool.ruff.lint]`            | `ignore = ["D100", "D101"]`                | Docstrings are required on functions, not on modules or Pydantic models.      |
| `[tool.ruff.lint.pydocstyle]` | `convention = "numpy"`                     | Docstrings follow the NumPy style.                                            |
| `[tool.pyright]`              | `typeCheckingMode = "standard"`            | Pyright checks types at its default level.                                    |
| `[tool.pyright]`              | `venvPath = "."`, `venv = ".venv"`         | Pyright finds the installed packages in `.venv/`.                             |

Run the checks in the project root:

```bash
uv run ruff check            # lint rules
uv run ruff format --check   # formatting, without changing files
uv run pyright               # type checks
```

**Notes:**

- **`--bare`:** plain `uv init` also creates a sample `main.py`, `README.md` and `.python-version`. The real `main.py` comes in Phase 1, and the repository already has a README.
- **Python version:** Ruff reads `requires-python = ">=3.14"` from `[project]`, so it needs no target version of its own.
- **Formatter defaults:** Ruff's formatter uses double quotes and a line length of 88, so it needs no settings.
- **Standard, not strict:** strict mode would flag every asyncpg record in a later phase, because asyncpg's types are incomplete.
- **Editor:** VS Code's Pylance reads `[tool.pyright]` too, so the editor finds the packages in `.venv/`. It takes the Python version from the selected interpreter, though. With the system Python (3.10), it marks newer names such as `datetime.UTC` (Python 3.11) in red. Run **Python: Select Interpreter** once and pick `./.venv/bin/python`.
- **Node.js:** Pyright is written in TypeScript. The PyPI package is a wrapper that uses `nodeenv` to get Node.js when it is not installed.

<br>

## 4. Add FastAPI and run the server

Add FastAPI with its standard extra:

```bash
uv add "fastapi[standard]"
```

Start the server in the project root:

```bash
uv run fastapi dev app/main.py
```

- **API:** `http://127.0.0.1:8000/api/...`
- **Swagger UI:** `http://127.0.0.1:8000/docs`, where every route can be called by hand.

Check the endpoints with `blog.http` (the VS Code REST Client extension). Run the requests from top to bottom: the write requests come after the mock login, because they need its session cookie.

**Notes:**

- **`[standard]` extra:** it adds the `fastapi` command and the Uvicorn server. Without it, `fastapi dev` does not exist.
- **`fastapi dev`:** it restarts the server on every saved file. `fastapi run` starts it without reloading, as in production.
- **`app/__init__.py`:** it makes `app/` a package. Without it, `fastapi dev` loads `main.py` as a top-level module, and the `from app.… import …` lines fail.
- **REST Client cookies:** REST Client keeps the cookies between requests, so every request after the mock login is signed in until the mock logout.

<br>

## 5. Start the PostgreSQL database

The database runs in a Docker container. The files come from the plan in `content-hub-blog-api-design`:

| File                  | Holds                                                                                   |
| --------------------- | --------------------------------------------------------------------------------------- |
| `docker-compose.yaml` | The `postgres:18` service, the `pgdata` volume, and the `db/init` and `db/seed` mounts  |
| `db/init/`            | `01-schema.sql` (the tables) and `02-seed.sql` (loads the CSV files with `COPY`)        |
| `db/seed/`            | One CSV file per table                                                                  |
| `.env.example`        | The variable names: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL` |

**Port clash:** only one container can publish port 5432. Stop any other PostgreSQL container first, or `up` fails with "port is already allocated".

In the project folder:

```bash
cp .env.example .env    # then set real values in .env
docker compose up -d
docker compose ps
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();"'
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*) FROM post;"'
```

- **`sh -c`:** runs the command inside the container, where `POSTGRES_USER` and `POSTGRES_DB` are already set from `.env`. The command works as it is, with no values to replace.
- **Single quotes outside:** the host shell passes the whole command to the container unchanged.
- **Double quotes inside:** the container's shell fills in the two variables and passes the SQL to `psql` as one argument.
- **Never type `<user>` as it is:** in bash, `<` reads input from a file, so `-U <user>` fails with "user: No such file or directory".

**Expected result:**

- `docker compose ps` shows the `db` service with the status `Up`.
- `psql` prints one row that starts with `PostgreSQL 18.`.
- The post count is `13`, the rows of `db/seed/post.csv`.
- `psql` does not ask for a password. It runs inside the container and connects through a local socket, which the image trusts. The password matters only for connections from outside the container, such as the FastAPI app.

**Notes:**

- **Init scripts run once:** the image runs `db/init/*.sql` only when the `pgdata` volume is empty. After a change to the schema or the seed, recreate the volume with `docker compose down -v`, then `docker compose up -d`.
- **Wait a few seconds:** `up -d` returns as soon as the container starts. Postgres then runs the init scripts and restarts, so a `psql` call right away fails with `No such file or directory` on its socket. The logs show when it is ready: `docker compose logs db | grep 'ready to accept'`.
- **One volume per project:** Compose names the volume after the folder (`content-hub-react-fastapi-postgresql_pgdata`), so this database is separate from the Express one.

<br>

## 6. Connect FastAPI to the database

Add the database driver and the settings package:

```bash
uv add asyncpg pydantic-settings
```

[app/db.py](app/db.py) holds the connection pool, and [app/main.py](app/main.py) passes its `lifespan` to `FastAPI()`:

| Name           | Does                                                                                  |
| -------------- | ------------------------------------------------------------------------------------- |
| `Settings`     | Reads `DATABASE_URL` from the environment, or else from `.env`                        |
| `lifespan`     | Opens the pool at start-up (before `yield`) and closes it at shutdown (after `yield`) |
| `DbConnection` | A dependency with `yield`: one connection per request, given back when it ends        |

Start the server in the project root, with the database container running:

```bash
uv run fastapi dev app/main.py
```

**Expected result:** `Application startup complete.` `asyncpg.create_pool` opens its first connections at once, so this line proves that the URL, user and password in `.env` work. With the container stopped, start-up fails with a connection error instead.

**Notes:**

- **`asyncpg`:** an async driver, so a query waits on the event loop, like the `async def` routes, and blocks no thread.
- **`pydantic-settings`:** `fastapi[standard]` installs it already, but `app/db.py` imports it, so it is listed in `dependencies` too. A missing `DATABASE_URL` stops start-up with `database_url: Field required`.
- **`extra="ignore"`:** `.env` also holds the `POSTGRES_*` keys for Compose. Without it, `Settings` rejects them with `extra_forbidden`.
- **Two Pyright hints:** Pyright does not know that `pydantic-settings` fills `database_url`, so `Settings()` has a `pyright: ignore`. `pool.acquire()` gives a proxy that gets the `Connection` methods only at runtime, so `get_connection` casts it to `asyncpg.Connection`.

<br>

## 7. CI workflow

[`ci.yml`](.github/workflows/ci.yml) holds one job, `backend`. It runs on a pull request, on a push to `main`, and by hand from the Actions tab:

| Step                         | Does                                                                             |
| ---------------------------- | -------------------------------------------------------------------------------- |
| `astral-sh/setup-uv`         | Installs uv and caches its downloads; the cache key comes from `uv.lock`         |
| `uv sync --locked`           | Installs the dependencies; fails if `uv.lock` no longer matches `pyproject.toml` |
| `uv run ruff check`          | Checks the lint rules                                                            |
| `uv run ruff format --check` | Checks the formatting, without changing files                                    |
| `uv run pyright`             | Checks the types                                                                 |

**Expected result:** the **CI / backend** check on the pull request passes every step.

**Notes:**

- **One file:** all checks start on the same events. One file declares the trigger, the permissions and the cancel rule once, and GitHub shows the result as one CI run.
- **One job:** the checks share one `uv sync`. A second job would set up uv and install the same packages again.
- **The same checks as on the laptop:** the job runs the commands from **Code checks** in `CLAUDE.md`, with the settings from `pyproject.toml`, so a local run and the CI run check the same rules.
- **No Python set-up step:** uv installs a Python version that matches `requires-python` in `pyproject.toml`.
- **Markdown excluded from Ruff:** Ruff also formats the Python code blocks inside Markdown files. The snippets in the docs are teaching examples, so `extend-exclude = ["*.md"]` in `pyproject.toml` limits Ruff to the `.py` files.
- **Later, a `frontend` job:** when the React client arrives, it gets its own job. Each job then installs only its own lock file, and a failure names the area.
- **Separate files instead:** useful when the apps need different triggers, for example a backend workflow that runs only when `app/` changes. Here every check runs on every change, so one file is enough.

<br>

## 8. Move the backend into backend/

The backend moves into its own folder, so the React client can sit next to it in `frontend/`:

```bash
mkdir backend
git mv app pyproject.toml uv.lock backend/
cd backend
uv sync   # creates backend/.venv/
```

| File or folder                       | Change                                                                              |
| ------------------------------------ | ----------------------------------------------------------------------------------- |
| `backend/app/db.py`                  | `env_file="../.env"`: the server runs from `backend/`, and `.env` stays in the root |
| `.github/workflows/ci.yml`           | The `backend` job runs in `backend/` (`defaults.run.working-directory`)             |
| `db/`, `docker-compose.yaml`, `.env` | Stay in the root: Compose reads `.env` there, and both apps share the database      |

**Expected result:** `uv run fastapi dev app/main.py` in `backend/` starts the server on port 8000, and `GET /api/blog` returns the posts.

**Notes:**

- **`git mv`:** Git records each file as renamed, so `git log --follow` still shows its history.
- **`env_file` is relative to the working directory:** pydantic-settings looks for `.env` in the folder the server starts in, not next to `db.py`.
- **`defaults.run` does not reach actions:** it sets the folder for `run:` steps only, so `setup-uv` gets its own `working-directory: backend` to find `uv.lock`.
- **Editor:** the old root `.venv/` is no longer used. In VS Code, run **Python: Select Interpreter** and pick `./backend/.venv/bin/python`.

<br>

## 9. Set up the React frontend

Create the Vite app in the project root, then add the packages in `frontend/`:

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install react-router tailwindcss @tailwindcss/vite
npm install -D -E prettier@3.10.1 prettier-plugin-tailwindcss@0.8.1
volta pin node@24.14.0
```

| File                       | Holds                                                                                    |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| `vite.config.ts`           | The React and Tailwind CSS plugins; the dev proxy from `/api` to `http://localhost:8000` |
| `src/globals.css`          | `@import 'tailwindcss'` and the `@theme` with the brand colours and fonts                |
| `index.html`               | The Google Fonts links (Raleway, Poppins) and the page title                             |
| `package.json`             | `volta.node` and the `prettier` and `prettier:format` scripts                            |
| `.prettierrc.json`         | Single quotes and `prettier-plugin-tailwindcss`, which reads `src/globals.css`           |
| `.github/workflows/ci.yml` | A `frontend` job: `npm ci`, ESLint, Prettier, then `npm run build`                       |

**Expected result:** `npm run dev` in `frontend/` shows the "Bloom & Burr" heading in Raleway on a latte-tan band at `http://localhost:5173`, and `http://localhost:5173/api/blog` returns the same posts as port 8000.

**Notes:**

- **Template content removed:** the counter demo, its CSS and its images are deleted; the components from the Express repo replace them on a later branch.
- **Dev proxy:** the browser calls only `localhost:5173`, and Vite forwards `/api` to FastAPI. The browser sees one origin, so the API needs no CORS middleware, and the mock session cookie is sent with each request.
- **Theme in CSS:** Tailwind CSS v4 has no `tailwind.config.js`. Each `@theme` variable becomes classes, for example `--color-latte-tan` gives `bg-latte-tan`. `--color-*: initial` removes the default palette, so only brand colours exist.
- **Volta in `frontend/package.json`:** the Express repo pins Node.js in a root `package.json`, which also holds Husky and lint-staged. This repo has one Node.js project, so the pin sits in `frontend/package.json`, and CI reads it through `setup-node`'s `node-version-file`.
- **Exact Prettier versions:** a new Prettier or plugin release can change the formatting, so `-E` saves `3.10.1`, not `^3.10.1`.
- **Prettier checks `frontend/` only:** the Markdown and YAML files in the root are not checked, because that would need a root `package.json`.
