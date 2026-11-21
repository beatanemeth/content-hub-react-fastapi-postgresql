# Rules: commits, branches and pull requests

| Item                    | Standard                                                                                |
| ----------------------- | --------------------------------------------------------------------------------------- |
| **Commit messages**     | [Conventional Commits](https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13) |
| **Branch names**        | [Conventional Branch](https://conventionalbranch.org/)                                  |
| **Pull request titles** | The same format as a commit message                                                     |

<br>

## Commit messages

```text
<type>(<optional scope>): <description>
```

- **Subject line only:** no body, no footer, no trailers (including `Co-Authored-By`).
- **Description:** imperative, present tense ("add", not "added"); lowercase first letter; no full stop at the end.
- **Breaking change:** add `!` before the colon (for example, `feat!: rename /posts to /articles`). Explain it in the pull request description.
- **Revert commits:** keep Git's default subject (`Revert "<reverted commit subject line>"`).

### Spelling

Only the first letter of the description is lowercase. Every other word keeps its normal case.

| Word kind         | Rule                                | Example                                          |
| ----------------- | ----------------------------------- | ------------------------------------------------ |
| **File names**    | Exactly as on disk (case-sensitive) | `docs: add README.md`                            |
| **Proper nouns**  | Official spelling                   | `build: upgrade FastAPI to 0.162`                |
| **Abbreviations** | Uppercase                           | `feat: add JSON body parsing`                    |
| **Identifiers**   | Exactly as in the code              | `feat: add require_user dependency`              |
| **Disciplines**   | Capitalised, as in `writer_docs.md` | `docs: describe the Data Engineering side track` |
| **Other words**   | Lowercase                           | `feat: add health check endpoint`                |

- **Start with a verb:** an imperative verb (`add`, `fix`, `rename`) as the first word avoids any clash with a proper noun or file name.
- **No backticks:** plain text with the exact case is enough.
- **British English:** as in `writer_british_english.md` (e.g., _optimise_, _behaviour_).

### Types

| Type       | Use for                                                                                                                                                                                   |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `feat`     | A new capability: routes, dependencies, Pydantic models, React components                                                                                                                 |
| `fix`      | A bug fix in a previously added feature                                                                                                                                                   |
| `refactor` | Restructuring without a behaviour change                                                                                                                                                  |
| `perf`     | A refactor that improves performance                                                                                                                                                      |
| `style`    | Formatting only (for example, Ruff format or Prettier)                                                                                                                                    |
| `test`     | Adding or correcting tests                                                                                                                                                                |
| `docs`     | Documentation only                                                                                                                                                                        |
| `build`    | Dependencies: `pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`; `tsconfig.json`                                                                                           |
| `ops`      | CI workflows, linter, formatter and type-checker settings (Ruff, Pyright, ESLint), even in `pyproject.toml`; the infrastructure code in `terraform/`, with its mocked tests and lock file |
| `chore`    | Maintenance: `.gitignore`, housekeeping                                                                                                                                                   |

### Scopes

Optional. Use the scope of the top-level folder the commit changes.

| Scope       | Covers                  |
| ----------- | ----------------------- |
| `backend`   | `backend/`              |
| `frontend`  | `frontend/`             |
| `claude`    | `CLAUDE.md`, `.claude/` |
| `terraform` | `terraform/`            |

Never use an issue number as a scope.

### Preparing a commit

Use `/commit`. It shows the commands in one code block, then runs them; each one asks for the maintainer's approval (an **ask** rule in `settings.json`).

```bash
git add <path> <path>
git commit -m "chore(claude): add Claude rules and settings"
```

- **Stage by path:** name each file or folder. Never `git add .`, `git add -A` or `git commit -a`.
- **One logical change per commit:** if the changes have different types or scopes, give one pair of commands per group.
- **Never stage:** `.env` files, `.venv/`, `__pycache__/`, `.ruff_cache/`, `node_modules/`, `.claude/settings.local.json`.

<br>

## Branches

```text
<type>/<description>
```

- **Types:** `feature/` for new capabilities, `fix/` for bug fixes, `release/` for the maintenance branch of a released version, `chore/` for everything else. Choose by the branch's main purpose; the commits inside keep their own types.
- **Description:** lowercase letters, digits and hyphens only. A `release/` branch takes the version tag, dots included (`release/v0.3.0`).

| Work                                               | Branch                                           | Commit types inside |
| -------------------------------------------------- | ------------------------------------------------ | ------------------- |
| **Claude set-up**                                  | `chore/claude-setup`                             | `chore(claude)`     |
| **Project set-up** (pyproject.toml, Vite)          | `chore/project-init`                             | `build`, `feat`     |
| **Coding style** (Ruff, Pyright, ESLint, Prettier) | `chore/code-style`                               | `build`, `ops`      |
| **Documentation**                                  | `chore/readme`                                   | `docs`              |
| **Dependency upgrade**                             | `chore/upgrade-fastapi`                          | `build`             |
| **Refactor**                                       | `chore/split-post-routes`                        | `refactor`          |
| **Routes and dependencies**                        | `feature/posts-routes`, `feature/mock-session`   | `feat`              |
| **Bug fix**                                        | `fix/post-id-parsing`                            | `fix`               |
| **Release maintenance**                            | `release/v0.3.0`                                 | `fix`, `build`      |
| **Deployment integration**                         | `feature/cloud-run-deployment`                   | merge commits only  |
| **Deployment step**                                | `chore/deployment-plan`, `chore/container-image` | one per change      |

- **One topic per branch:** one branch and one pull request per topic. Never commit on `main`.

<br>

## Pull requests

- **Title:** a commit subject line (for example, `feat: add CRUD routes for posts`).
- **Merge commit title:** `chore: merge PR#<number> from <branch>` (for example, `chore: merge PR#4 from feature/posts-routes`).

### Description

- **Keep it concise:** write a 1–2 sentence summary explaining what changed and why. Avoid multi-heading essays or repeating rationale already documented in the code or commit history.
- **Link related pull requests:** include their full URLs, if there are any.
- **Reference issues at the end:** close the description with `Closes #<number>` when the pull request resolves a GitHub issue (or `Refs #<number>` when it does not resolve it). Without an issue, leave this out.
- **Attribution:** keep the "🤖 Generated with Claude Code" line.
