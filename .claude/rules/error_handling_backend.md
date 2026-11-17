---
paths:
  - '*.py'
  - 'src/**/*.py'
  - 'backend/**'
---

# Rules: minimal error handling in the backend

- **`HTTPException` for expected errors:** a handler raises `HTTPException(status_code=..., detail="...")`. FastAPI turns it into a JSON response; the handler never builds an error response itself.
- **One error key:** every JSON error body has a `detail` key, as FastAPI writes it. Do not rename it or wrap it in another shape.
- **No `try/except` for unexpected errors:** let them propagate. FastAPI answers `500` and logs the traceback on the server.
- **Keep the built-in handlers:** do not override FastAPI's handlers for `HTTPException` or `RequestValidationError`. Add an exception handler only for errors FastAPI does not know, such as database errors (Phase 4 of the [backend roadmap](../../docs/claude/evolution_roadmap_backend.md)).
- **Explicit status codes:** set `status_code` in the decorator when success is not `200`: `201` for create and `204` for delete.

<br>

## Example: a missing resource

```python
from fastapi import HTTPException

for post in posts:
    if post.id == post_id:
        return post
raise HTTPException(status_code=404, detail="Post not found")
```

The client receives `404` with `{"detail": "Post not found"}`.

<br>

## Three places send errors

- **Route handlers:** raise `HTTPException`, for example `404 "Post not found"`.
- **FastAPI itself:** answers the errors in the table below, from Phase 1 on, with no code.
- **The database exception handler (Phase 4):** turns asyncpg errors, such as an unknown `author_id`, into `422` with a `detail` message.

Any route can return these built-in errors, so the contract table in [api_endpoints.md](../../docs/claude/api_endpoints.md) does not repeat them:

| Status | Body                                      | When                                                             |
| ------ | ----------------------------------------- | ---------------------------------------------------------------- |
| `404`  | `{"detail": "Not Found"}`                 | No route matches the path.                                       |
| `405`  | `{"detail": "Method Not Allowed"}`        | The path exists, but not with this method.                       |
| `422`  | `{"detail": [{"type", "loc", "msg", …}]}` | Broken JSON, a missing or invalid field, or a non-integer id.    |
| `500`  | `Internal Server Error` (plain text)      | An unexpected error. The traceback is logged on the server only. |

<br>

## What the client must handle

- **`detail` is a string or a list:** a string for `HTTPException` (`400`, `401`, `404`) and for the Phase 4 errors, and a list for `422` validation errors. The list items carry `loc` and `msg`; see [validation_backend.md](./validation_backend.md).
- **`500` is not JSON:** the body is plain text, so the client must not parse it as JSON.
