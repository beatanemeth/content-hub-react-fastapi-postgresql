# Workaround for the out-of-scope parts

> This is a blog app for a fictional coffee company. To keep it simple, it has no sign-in or sign-up. A mock session stands in for them, so the FastAPI server has the blog post endpoints that a real app would need, plus a few endpoints that exist only for the mock. The missing parts needed a workaround, and this file explains it.

> **The workaround in short:**
>
> - The author is **never in the request body**. A fake login sets a session cookie, and the backend takes the author from it.
> - **Only staff can log in.** So a logged-in user is always staff and may write.
> - The frontend sends category and tag **labels**. The backend looks up their ids and stores ids.
> - The frontend has **no hard-coded lists**: it loads the staff, categories and tags from the API.

<br>

## API endpoints

The full contract is in [api_endpoints.md](../claude/api_endpoints.md).

Blog posts. Reading is public; writing needs a mock session:

| Method   | Path                  | Purpose        | Access | Success           | Errors                                  |
| -------- | --------------------- | -------------- | ------ | ----------------- | --------------------------------------- |
| `GET`    | `/api/blog`           | List all posts | Public | 200, array        | 500                                     |
| `GET`    | `/api/blog/{post_id}` | Read one post  | Public | 200, the post     | 404, 422, 500                           |
| `POST`   | `/api/blog`           | Create a post  | Staff  | 201, the new post | 400 (unknown label), 401, 422, 500      |
| `PUT`    | `/api/blog/{post_id}` | Replace a post | Staff  | 200, the post     | 400 (unknown label), 401, 404, 422, 500 |
| `DELETE` | `/api/blog/{post_id}` | Delete a post  | Staff  | 204, no body      | 401, 404, 422, 500                      |

Form options, public and read-only:

| Method | Path              | Returns           | Called from             |
| ------ | ----------------- | ----------------- | ----------------------- |
| `GET`  | `/api/categories` | `[{ id, label }]` | the category checkboxes |
| `GET`  | `/api/tags`       | `[{ id, label }]` | the tag checkboxes      |

**Mock only:** the endpoints below exist only because there is no real sign-in. A real app has its own sign-in routes in their place. See [Author: the mock session](#author-the-mock-session).

| Method | Path               | Body            | Success                                  | Errors                                | Called from          |
| ------ | ------------------ | --------------- | ---------------------------------------- | ------------------------------------- | -------------------- |
| `GET`  | `/api/authors`     | none            | 200 `[{ id, full_name }]`                | 500                                   | `/docs` or `blog.http` |
| `POST` | `/api/mock-login`  | `{ person_id }` | 200 `{ id, full_name }`, sets the cookie | 401 `Unknown staff member`, 422       | `/docs` or `blog.http` |
| `POST` | `/api/mock-logout` | none            | 204, clears the cookie                   | none                                  | `/docs` or `blog.http` |
| `GET`  | `/api/me`          | none            | 200 `{ id, full_name }`                  | 401 `Not signed in`                   | `/docs` or `blog.http` |

An unknown route gets `404 {"detail": "Not Found"}`. A body that is not valid JSON gets `422`.

Each router has a tag (`blog`, `options`, `session`), which groups its routes in `/docs`.

### API implementation

The API was built in three stages:

1. **In-memory FastAPI:** tested with the REST Client extension in VS Code (`blog.http`). Its first request is `POST /api/mock-login`; REST Client keeps the cookie for the requests after it.
2. **FastAPI with PostgreSQL:** the handlers query the database through `asyncpg`. The same `blog.http` works, because the API is the same.
3. **React frontend:** it calls the API through the Vite proxy (`/api` → `http://localhost:8000`). The browser sees one origin, so the backend needs no CORS and the session cookie is same-origin. The app has no login page: the cookie comes from `POST /api/mock-login` in the Swagger UI at `http://localhost:8000/docs`, in the same browser (see [README.md: log in to write posts](../../README.md#log-in-to-write-posts)). A login in `blog.http` does not reach the browser, because REST Client keeps its own cookies.

FastAPI also serves interactive API docs at `/docs` (from `/openapi.json`), built from the route signatures and the Pydantic models. The session cookie is declared as a security scheme (`APIKeyCookie`), so the routes that need a logged-in user have a lock icon. To try them in `/docs`, run `POST /api/mock-login` there first: the browser keeps the cookie and sends it with the next requests.

<br>

## Out of scope

The list is in [NOTES.md: out of scope](../../NOTES.md#out-of-scope).  
In short: there is no sign-in or sign-up, only a mock session, and validation and error handling are simple. The sessions live in the server's memory, so a restart logs everyone out, and the server must run as one process (no `--workers 2`).

<br>

## Blog pages

### Blog list page

Each card shows:

- the title
- the published date and the author name, separated by `•`
- the summary

### Single post page

The page shows:

- the title
- the author, the published date and the reading time
- the summary
- the categories
- the body
- the tags

### Create and edit post

The form's fields:

- title: text
- categories: checkboxes filled from `GET /api/categories`; choose one or more
- tags: checkboxes filled from `GET /api/tags`; choose one or more
- published date: `<input type="date">`
- summary: text
- body: text

Every field is required, and each checkbox group needs at least one ticked box. There is no author field: the author is whoever is logged in.

<br>

## Workaround: the chosen solution

### Author: the mock session

You fake the session, not the author. A fake login gives the browser a session cookie, and a dependency turns that cookie back into the current user. The routes take the author from there. Later, when real sign-in arrives, you replace only the login routes and the session store. The post routes stay as they are.

- **`POST`:** the author is the logged-in user.
- **`PUT`:** the author **stays the original author**. Any staff member may edit any post, and `updated_at` shows that it changed.
- **`DELETE`:** any staff member may delete any post.
- **Staff check:** it happens at login, so "logged in" means "staff", and the write routes need no second check and no 403. With PostgreSQL (Stage 2), the backend also checks the staff row on every request that needs a logged-in user. A staff member removed while logged in loses the session at their next write or `GET /api/me`.

#### What it copies from a real app

|                             | Mock session (cookie)                                                                 |
| --------------------------- | ------------------------------------------------------------------------------------- |
| Real-world pattern          | A session cookie, as with Starlette's `SessionMiddleware` and most same-site web apps |
| Login step                  | Yes: the server issues the identity and sets the cookie                               |
| What the client holds       | An opaque session id (a random UUID), not the user id                                 |
| Who attaches it             | The browser, automatically                                                            |
| Can frontend JS read it?    | No: the cookie is `httponly`                                                          |
| Logout and "who am I?"      | Built as in real life: `POST /api/mock-logout`, `GET /api/me`                         |
| Security topic it brings up | CSRF: `SameSite=Lax` stops other sites from sending the cookie with a POST            |
| What is fake                | No password, and the session store is a `dict` that a restart empties                 |

### Categories and tags

- The frontend sends the labels in `categories` and `tags`, for example `["BeanScience"]`.
- Each checkbox is built from one row of `GET /api/categories` or `GET /api/tags`. Its `value` is the label, because the label is what the body sends.
- The labels are `UNIQUE` in the database, so a label finds exactly one row. The backend looks up the ids and stores them in `post_category` and `post_tag`.
- An unknown label gets a 400 that names every unknown label, for example `Unknown category: NoSuchCategory, AlsoMissing`. Categories are checked before tags.
- The labels are not trimmed, so each must match exactly: `" Inspiring"` is an unknown tag.
- The API returns the categories and tags as `{ id, label }` objects. The edit form pre-ticks its boxes from them.

### Date

- The frontend sends `published_on` from `<input type="date">`, which is already in the form `YYYY-MM-DD`.
- Pydantic reads it into a Python `date` and rejects an impossible date, so `2026-02-30` gets a 422. asyncpg needs a `date` for a `date` column; it does not accept text there.
- The backend sets `updated_at` (`now()` in SQL, `datetime.now(UTC)` in memory). The client never sends it.

### Minutes to read

The backend calculates the reading time in Stages 1 and 2: 200 words per minute, and at least 1 minute. In Stage 3, the frontend takes it over, and the backend's `minutes_to_read` field and function are removed.

<br>

## Validation

- **Frontend:** every field has the `required` attribute. In a checkbox group, every box is `required` until one is ticked (`required={selected.length === 0}`).
- **Backend:** the Pydantic types check, before the route runs, that:
  - `title`, `summary` and `body` are strings; they are trimmed and must not be empty then
  - `published_on` is a real date
  - `categories` and `tags` are non-empty lists of non-empty strings; repeated labels are removed (`["A", "A"]` → `["A"]`)
  - no text field and no label contains the NUL character, which a PostgreSQL `text` column cannot hold
  - `person_id` at login, and the post id in the URL, are whole numbers from 1 to 2147483647, the largest PostgreSQL `integer`
  - a field the model does not name, such as `author_id`, is ignored
- **PostgreSQL:** the `NOT NULL` constraints, the `UNIQUE` labels and the foreign keys.

Pydantic's default (lax) mode converts a value when the conversion is safe: `"1"` is read as the `person_id` 1, but `1.5` is a 422.

The order of the checks on `POST` and `PUT`: 401 (not logged in), then 422 (the id and the body, every invalid field at once), then 400 (unknown label), then 404 (`PUT`: no post has this id). The one exception: broken JSON is a 422 even without a session, because FastAPI reads the body before it runs the dependencies.

<br>

## Error handling

There are no exception handlers: every error has FastAPI's default form.

- **422 Unprocessable Content**, for invalid input: `{ "detail": [ … ] }`, one item per problem, each with `loc` (where: `["body", "title"]`, `["path", "post_id"]`), `msg` (a readable message) and `type` (a code such as `string_too_short`).
- **Every other error**, raised as `HTTPException(status_code, detail=message)`: `{ "detail": "<message>" }`.

Written by the routes and the dependencies:

| Status | `detail`                                       | When                                                                                |
| ------ | ---------------------------------------------- | ----------------------------------------------------------------------------------- |
| 400    | `Unknown category: X, Y` or `Unknown tag: X, Y` | names every unknown label                                                           |
| 401    | `Unknown staff member`                         | mock login with an id that is not staff                                             |
| 401    | `Not signed in`                                | a write, or `GET /api/me`, without a live session, or (Stage 2) without a staff row |
| 404    | `Post not found`                               | no post has this id                                                                 |

Written by FastAPI and Starlette:

| Status | `detail`                 | When                                                                                                                                                                                          |
| ------ | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 422    | a list, one item a field | a body or URL id that fails its type: broken JSON, no body, a list instead of an object, a non-JSON `Content-Type`, an empty title, an impossible date, an empty list, a NUL, `abc` as the id |
| 404    | `Not Found`              | no route matched, for example `/api/blogs`                                                                                                                                                    |
| 405    | `Method Not Allowed`     | the path exists, but not with this method, for example `PATCH /api/blog/1`                                                                                                                    |
| 500    | `Internal Server Error`  | anything else, as plain text; uvicorn logs the traceback                                                                                                                                      |

- **Deleted label during a write:** a category or tag deleted between the label lookup and the `INSERT` breaks the foreign key, so the client gets a 500. Nothing in this API deletes categories or tags, so this gap is left open.
- **The 405's `Allow` header:** it names only `GET` for `/api/blog/1`. `GET`, `PUT` and `DELETE` on one path are three routes, and Starlette lists the methods of the first one that matches. It is a known Starlette limit, left as it is.
- **Frontend:** on a 422, the form shows each `msg` next to the field its `loc` names. On any other error, it shows `detail` as one message. A 500 body is plain text, not JSON.

<br>

## Database queries

- **One connection per request:** the `DbConnection` dependency lends each request one connection from the `asyncpg` pool. The route and `require_user` share it.
- **The list query:** only the columns the cards need, with the author as one `{ id, full_name }` object (`json_build_object`). The posts are sorted by `published_on DESC, id DESC`.
- **The single post query:** adds the body, `updated_at`, and the categories and tags as `{ id, label }` lists (`json_agg` in subqueries; `COALESCE` turns no rows into `[]`). A JSON codec on each connection parses these columns into Python lists and dicts.
- **Label lookup:** `SELECT id, label FROM category WHERE label = ANY($1::text[])`, and the same for `tag`. It runs before the transaction, because it only reads.
- **POST:** `async with db.transaction()` → `INSERT` the post `… RETURNING id` → one `INSERT … SELECT $1, unnest($2::int[])` per link table → read the post back before `COMMIT`. An exception inside the block rolls everything back, so a 500 means nothing was saved.
- **PUT:** `UPDATE` the post `… RETURNING id` (no row → 404, raised inside the block, which rolls back), then `DELETE` its link rows and insert the new ones, and read the post back, all in one transaction. The `UPDATE` does not touch `author_id`.
- **DELETE:** one statement, `… RETURNING id` (no row → 404), with no transaction. `ON DELETE CASCADE` removes the link rows.

<br>

## Assumptions

1. **Only staff write posts:** the backend enforces it. The mock login accepts only staff, and the write routes need a session.
2. **Any staff member may edit or delete any post:** it is a shared team blog. The author of a post never changes.
3. **Categories, tags and staff come from the database:** the frontend loads them from the API, so a new category appears in the form without a code change.
4. **The API returns joined data:** the author as `{ id, full_name }`, and the categories and tags as `{ id, label }`. The frontend needs no lookups.
5. **The date belongs to the author:** the author picks it; it is not set automatically.
6. **`minutes_to_read` moves to the frontend in Stage 3:** until then, the backend calculates it.
7. **The list returns only what the cards show:** the body, `updated_at`, categories and tags come only with a single post.
8. **One server process:** the sessions, and the in-memory posts of Stage 1, live in the memory of one process.
