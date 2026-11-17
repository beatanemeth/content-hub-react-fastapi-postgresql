# Backend evolution roadmap (phased approach)

This guide outlines the step-by-step evolution of the FastAPI backend for our study project. Each phase uses what FastAPI, Pydantic and asyncpg already provide before any custom code. The API contract in [api_endpoints.md](./api_endpoints.md) stays the same in every phase.

> **Shortened examples:** the `Post` model below has only `id`, `title`, `summary` and `body`. The full field list is in [api_endpoints.md](./api_endpoints.md#post-fields).

<br>

## Phase 1: in-memory storage and a single file

**Goal:** establish the request-response cycle with no database.

- **Storage:** Python lists in `main.py` (posts, categories, tags and staff) and a `dict` of sessions. They reset on every server restart.
- **Validation:** Pydantic models. FastAPI checks the request body before the handler runs and answers `422` when it is invalid.
- **Errors:** `raise HTTPException(...)`. FastAPI turns it into a JSON response with a `detail` key.

### Steps

Each step adds one concept, and all the code stays in `main.py`. A step uses only what the steps before it built, so no temporary code is needed.

1. **In-memory data and option routes:** the categories, tags and staff as lists of Pydantic models; `GET /api/categories` and `GET /api/tags`. Concept: a route handler with a `response_model`.
2. **Mock session:** `GET /api/authors`, `POST /api/mock-login`, `POST /api/mock-logout` and `GET /api/me`, with the sessions in a `dict`. The `require_user` dependency turns the session cookie into the current user, or answers `401 Not signed in`. It reads the cookie with `APIKeyCookie(auto_error=False)`, so a missing cookie gets the same `401` as an unknown session. Concept: cookies and the first `Depends`.
3. **Post routes:** the five routes on `/api/blog`, with the posts in a list. The write routes take the author from `require_user` and look up the labels in the lists of step 1; an unknown label gets `400`. Concept: request and response models, status codes and `HTTPException`.

### Example code (`main.py`)

```python
from itertools import count
from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class PostIn(BaseModel):
    title: NonEmptyStr
    summary: NonEmptyStr
    body: NonEmptyStr


class Post(PostIn):
    id: int


app = FastAPI()

posts: list[Post] = []
post_ids = count(start=1)


@app.post("/api/blog", summary="Create a post", response_model=Post, status_code=201)
async def create_post(post_in: PostIn) -> Post:
    """Store a new post and return it with its id."""
    post = Post(id=next(post_ids), **post_in.model_dump())
    posts.append(post)
    return post


@app.get(
    "/api/blog/{post_id}",
    summary="Get one post",
    response_model=Post,
    responses={404: {"description": "Post not found"}},
)
async def get_post(post_id: int) -> Post:
    """
    Return one post by its id.

    Raises
    ------
    HTTPException
        404 if no post has this id.
    """
    for post in posts:
        if post.id == post_id:
            return post
    raise HTTPException(status_code=404, detail="Post not found")
```

<br>

## Phase 2: PostgreSQL with asyncpg

**Goal:** connect a real database through a connection pool and dependency injection.

- **Storage:** PostgreSQL through an asyncpg pool (`asyncpg.create_pool`). The **lifespan** opens the pool at start-up and closes it at shutdown.
- **Settings:** a `pydantic-settings` model reads `DATABASE_URL` from the environment, or else from `.env`. It ignores the `POSTGRES_*` keys that Compose reads from the same file.
- **Dependency:** `get_connection` lends each request one connection from the pool (`pool.acquire()`). The connection goes back to the pool when the request ends, after a success or an error.
- **Explicit transactions:** asyncpg commits each statement on its own. A write with several statements wraps them in `async with conn.transaction():`, which commits at the end of the block and rolls back when the block raises.
- **Records to models:** asyncpg returns `Record` rows; `Post(**dict(row))` turns one into a `Post` model.
- **JSON columns:** asyncpg returns a `json` column as text. A type codec, set in the pool's `init` function, parses it into Python lists and dicts.
- **No `try/except` in handlers:** FastAPI already answers an unhandled exception with `500` and logs the traceback.
- **In-memory data removed:** once every handler uses SQL, the `posts` list and `post_ids` are deleted.

### Example code (`app/db.py`, shortened)

```python
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, cast

import asyncpg
from fastapi import Depends, FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str


_pool: asyncpg.Pool | None = None


async def init_connection(connection: asyncpg.Connection) -> None:
    await connection.set_type_codec(
        "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    global _pool
    settings = Settings()  # pyright: ignore[reportCallIssue]
    _pool = await asyncpg.create_pool(settings.database_url, init=init_connection)
    yield
    await _pool.close()


async def get_connection() -> AsyncIterator[asyncpg.Connection]:
    if _pool is None:
        raise RuntimeError("The pool is not open: create the app with FastAPI(lifespan=lifespan)")
    async with _pool.acquire() as connection:
        yield cast(asyncpg.Connection, connection)


DbConnection = Annotated[asyncpg.Connection, Depends(get_connection)]
```

### Example route

```python
@app.get("/api/blog", summary="List all posts", response_model=list[Post])
async def list_posts(conn: DbConnection) -> list[Post]:
    """Return all posts, newest first."""
    rows = await conn.fetch(
        "SELECT id, title, summary, body FROM post ORDER BY published_on DESC, id DESC"
    )
    return [Post(**dict(row)) for row in rows]
```

<br>

## Phase 3: splitting into modules with `APIRouter`

**Goal:** keep `main.py` small as the queries grow.

FastAPI has no controller layer: the route handler is the controller. An `APIRouter` groups the post handlers in their own module, and `main.py` only creates the app and includes the router. The post SQL moves into a module of its own, so the route module only handles HTTP.

| Module                | Holds                                                                       |
| --------------------- | --------------------------------------------------------------------------- |
| `app/main.py`         | `app = FastAPI(lifespan=...)`, `app.include_router()`                       |
| `app/models.py`       | The Pydantic models (`PostIn`, `Post`)                                      |
| `app/db.py`           | `lifespan`, `get_connection` and `DbConnection`                             |
| `app/post_routes.py`  | The post route handlers, the transactions and the `HTTPException`s          |
| `app/post_queries.py` | The post SQL: functions that take a connection and return models or `None` |

- **Flat modules:** the modules stay in `app/`, with no `routers/` folder. For a few small modules, a folder adds import paths but makes nothing easier to find.
- **Queries know no HTTP:** a query function takes a plain `asyncpg.Connection` and returns a model, an id, `None` or `False`. It never raises `HTTPException`; the handler decides what "no row" means for the client (for example `404`).
- **Transactions stay in the handler:** the handler decides which statements succeed or fail together, so it opens `conn.transaction()` and calls the query functions inside it.
- **Short queries stay inline:** the option routes and the mock session have only one or two queries each, so their SQL stays in their own module.

### Example code

```python
# app/post_queries.py
import asyncpg

from app.models import Post


async def find_post(conn: asyncpg.Connection, post_id: int) -> Post | None:
    """Return one post, or None."""
    row = await conn.fetchrow(
        "SELECT id, title, summary, body FROM post WHERE id = $1", post_id
    )
    return None if row is None else Post(**dict(row))


# app/post_routes.py
from fastapi import APIRouter, HTTPException

from app import post_queries
from app.db import DbConnection
from app.models import Post

post_router = APIRouter(tags=["blog"])


@post_router.get(
    "/{post_id}",
    summary="Get one post",
    response_model=Post,
    responses={404: {"description": "Post not found"}},
)
async def get_post(post_id: int, conn: DbConnection) -> Post:
    """
    Return one post by its id.

    Raises
    ------
    HTTPException
        404 if no post has this id.
    """
    post = await post_queries.find_post(conn, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


# app/main.py
from fastapi import FastAPI

from app.db import lifespan
from app.post_routes import post_router

app = FastAPI(lifespan=lifespan)
app.include_router(post_router, prefix="/api/blog")
```

<br>

## Phase 4: exception handlers for database errors

**Goal:** answer expected database errors with a clear status instead of `500`.

FastAPI already answers unknown routes (`404`), wrong methods (`405`), invalid bodies (`422`) and unexpected errors (`500`); see [error_handling_backend.md](../../.claude/rules/error_handling_backend.md). What remains are the database's own rules. For example, an `author_id` that does not exist breaks a foreign key. One exception handler maps these asyncpg errors to a status and a message.

### Example code (`main.py`)

```python
from asyncpg.exceptions import IntegrityConstraintViolationError
from fastapi import Request
from fastapi.responses import JSONResponse

# SQLSTATE codes: https://www.postgresql.org/docs/current/errcodes-appendix.html
PG_ERROR_RESPONSE = {
    "23503": (422, "Author, category or tag not found"),  # foreign_key_violation
    "23505": (422, "Duplicate category or tag id"),  # unique_violation
}


@app.exception_handler(IntegrityConstraintViolationError)
async def integrity_error_handler(
    _request: Request, exc: IntegrityConstraintViolationError
) -> JSONResponse:
    response = PG_ERROR_RESPONSE.get(exc.sqlstate)
    if response is None:
        raise exc  # unexpected: FastAPI answers 500 and logs the traceback
    status_code, message = response
    return JSONResponse(status_code=status_code, content={"detail": message})
```

<br>

## Phase 5: reusable dependencies

**Goal:** remove logic that repeats across handlers.

- **`get_post_or_404`:** `GET`, `PUT` and `DELETE` on `/api/blog/{post_id}` all load one post or answer `404`. A dependency does this once. FastAPI caches dependencies per request, so it shares the same connection with the handler.
- **Middleware only on real need:** Uvicorn already logs every request, so a request logger adds nothing. Use `@app.middleware("http")` only for a concern that no dependency can cover.

### Example code (`app/post_routes.py`)

```python
from typing import Annotated

from fastapi import Depends, HTTPException


async def get_post_or_404(post_id: int, conn: DbConnection) -> Post:
    post = await post_queries.find_post(conn, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@post_router.get(
    "/{post_id}",
    summary="Get one post",
    response_model=Post,
    responses={404: {"description": "Post not found"}},
)
async def get_post(post: Annotated[Post, Depends(get_post_or_404)]) -> Post:
    """
    Return one post by its id.

    Raises
    ------
    HTTPException
        404 if no post has this id.
    """
    return post
```
