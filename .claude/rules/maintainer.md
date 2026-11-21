# Rules: working with the maintainer

## Profile

- Strong in **systems thinking**, Python, Docker and API-based ETL. Works on Linux.
- Writes in English as a second language.

<br>

## How to support the maintainer

- **FastAPI:** the maintainer is refreshing this knowledge. Explain the reasoning behind each route and middleware, not just the code. Keep explanations short and focused on what is non-obvious.
- **Wording:** use plain, precise English.

<br>

## Teaching pace

- **One step per reply:** one new file or one change, with one idea behind it. Then stop and wait for the maintainer.
- **Short explanations:** explain the one idea behind the step in a few sentences. Do not walk through code or commands line by line; the maintainer asks when a line or a command is unclear.
- **No quiz:** do not ask study questions before a new concept. Explain it; the maintainer asks when something is unclear.
- **Questions only for decisions:** ask when the maintainer must choose (a dependency, a folder, a new layer). Give one recommendation and its reason, not a list of options.
- **Build on what the maintainer knows:** compare with earlier project(s) below.

<br>

## Optional: the maintainer writes

**Off by default.** Use it only when the maintainer asks for it, for one task or for a whole session (for example, "I write, you review"). It ends with that task or session; otherwise, Claude writes the code as usual.

1. **Before:** explain the one idea behind the step and name the roadmap phase or rule it follows. Do not show the finished code.
2. **The maintainer writes** the file or the change.
3. **Review:** read it and run the quick checks (lint, format, type checks, `terraform validate` and `terraform test`). Explain each remark: what is wrong or unclear, which rule it breaks, and why.
4. **No rewriting:** Claude does not edit the file unless the maintainer asks for a specific fix. A short snippet in the reply may show what a remark means.
5. **Done:** when the checks pass and no remark is left, say so, then continue with the next step.
