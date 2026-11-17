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
- **Editor:** VS Code's Pylance reads `[tool.pyright]` too, so the editor finds the packages in `.venv/` without choosing an interpreter by hand.
- **Node.js:** Pyright is written in TypeScript. The PyPI package is a wrapper that uses `nodeenv` to get Node.js when it is not installed.
