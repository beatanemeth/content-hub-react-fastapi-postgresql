# Rules: British English

Use British English spelling (e.g., _analyse_, _optimise_, _colour_, _favour_, _capitalise_) in text written for this project. The rule depends on who defines the word, not on the file type.

**Apply to:**

- **Prose:** documentation, README, CLAUDE.md, `.claude/` files, commit messages, pull request descriptions.
- **Comments and docstrings** in any file, including `.py` and `.ts` files.
- **Names created in this project:** variables, functions, types, Pydantic models, dependencies, route handlers, file and script names.
- **API text:** JSON field names this API defines (for example, `colour`, not `color`) and error messages in responses.

**Do not apply to:**

- **Syntax and keywords** defined by a language or tool: the keys in `pyproject.toml`, `package.json` and `tsconfig.json`.
- **Library and API names:** Python, FastAPI, Pydantic and asyncpg identifiers (for example, `APIRouter`, `HTTPException`, `status_code`, `model_dump`); React and TypeScript identifiers in the frontend; HTTP header names and HTTP status texts (`Not Found`).
- **Library messages:** the error messages that FastAPI and Pydantic write themselves, such as `Method Not Allowed` or `String should have at least 1 character`. Only the messages this project writes (for example, `Post not found`) follow this rule.
- **Quotations and proper nouns**, such as product names and URLs.

**Abbreviations:**

- **`vs` without a full stop:** write "Phase 1 vs Phase 2", not "Phase 1 vs. Phase 2".
