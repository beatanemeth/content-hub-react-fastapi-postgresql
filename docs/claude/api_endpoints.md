# API endpoints

The API has one main resource: blog posts, under `/api/blog`. The backend runs at `http://localhost:8000`; the frontend runs at `http://localhost:5173` (Vite's default port). The frontend calls relative paths such as `/api/blog`, and the Vite dev server proxies them to the backend. The browser sees one origin, so the API needs no CORS, and the session cookie is same-origin.

There is no sign-in or sign-up. A mock session stands in for them: a fake login sets a session cookie, and the write endpoints answer `401` without it. Only staff can log in, so a logged-in user may create, edit and delete any post. The reasons are in [info_out_of_scope_workaround.md](../notes/info_out_of_scope_workaround.md).

**Storage:** the contract below is the same in every stage. Stage 1 keeps the posts in memory, which resets on every server restart. Stage 2 stores them in PostgreSQL.

<br>

## Post endpoints

| Method   | Path                  | Purpose        | Access | Called from                   |
| -------- | --------------------- | -------------- | ------ | ----------------------------- |
| `GET`    | `/api/blog`           | List all posts | Public | `/blog`                       |
| `GET`    | `/api/blog/{post_id}` | Read one post  | Public | `/blog/:id`, `/blog/:id/edit` |
| `POST`   | `/api/blog`           | Create a post  | Staff  | Save on `/blog/new`           |
| `PUT`    | `/api/blog/{post_id}` | Replace a post | Staff  | Save on `/blog/:id/edit`      |
| `DELETE` | `/api/blog/{post_id}` | Delete a post  | Staff  | Delete on `/blog/:id`         |

The "Called from" column uses React Router's path syntax (`:id`); the API paths use FastAPI's (`{post_id}`).

<br>

## Form options

Public and read-only. With these, the form has no hard-coded lists: when a category is added to the database, the form shows it.

| Method | Path              | Returns           | Called from             |
| ------ | ----------------- | ----------------- | ----------------------- |
| `GET`  | `/api/categories` | `[{ id, label }]` | the category checkboxes |
| `GET`  | `/api/tags`       | `[{ id, label }]` | the tag checkboxes      |

<br>

## Mock session endpoints

**Mock only:** these endpoints exist only because there is no real sign-in. A real app has its own sign-in routes in their place.

| Method | Path               | Body            | Success                                  | Failure                         | Called from          |
| ------ | ------------------ | --------------- | ---------------------------------------- | ------------------------------- | -------------------- |
| `GET`  | `/api/authors`     | None            | 200 `[{ id, full_name }]`, the staff     | None                            | `/docs` or `blog.http` |
| `POST` | `/api/mock-login`  | `{ person_id }` | 200 `{ id, full_name }`, sets the cookie | 401 `Unknown staff member`, 422 | `/docs` or `blog.http` |
| `POST` | `/api/mock-logout` | None            | 204, clears the cookie                   | None                            | `/docs` or `blog.http` |
| `GET`  | `/api/me`          | None            | 200 `{ id, full_name }`                  | 401 `Not signed in`             | `/docs` or `blog.http` |

<br>

## Contract

The contract is the agreement between the server and its clients: "If you send this request, you get this response." Error bodies are in [error_handling_backend.md](../../.claude/rules/error_handling_backend.md).

| Action   | Method and path              | Input                      | Output                          | Success | Failure                        |
| -------- | ---------------------------- | -------------------------- | ------------------------------- | ------- | ------------------------------ |
| List     | `GET /api/blog`              | None                       | `PostSummary` list, newest first | `200`   | None                           |
| Read one | `GET /api/blog/{post_id}`    | `post_id`                  | One `PostDetail`                | `200`   | `404`, `422`                   |
| Create   | `POST /api/blog`             | The post fields            | The new `PostDetail`            | `201`   | `400`, `401`, `422`            |
| Update   | `PUT /api/blog/{post_id}`    | `post_id`; the post fields | The updated `PostDetail`        | `200`   | `400`, `401`, `404`, `422`     |
| Delete   | `DELETE /api/blog/{post_id}` | `post_id`                  | No body                         | `204`   | `401`, `404`, `422`            |

- **`400`:** a category or tag label has no row. The message names every unknown label, for example `Unknown category: NoSuchCategory, AlsoMissing`.
- **`401`:** no live mock session (`Not signed in`).

<br>

## Post fields

### Request body of `POST` and `PUT` (`PostInput`)

| Field          | Type        | Rule                                                              |
| -------------- | ----------- | ----------------------------------------------------------------- |
| `title`        | `str`       | Trimmed, then not empty                                           |
| `summary`      | `str`       | Trimmed, then not empty                                           |
| `body`         | `str`       | Trimmed, then not empty                                           |
| `published_on` | `date`      | A real date in the form `YYYY-MM-DD`                              |
| `categories`   | `list[str]` | Category **labels**, at least one; each must exist (else `400`)   |
| `tags`         | `list[str]` | Tag **labels**, at least one; each must exist (else `400`)        |

- **No author field:** the author is the logged-in user. A field the model does not name, such as `author_id`, is ignored.
- **Labels, not ids:** the backend looks up the ids and stores ids. Labels are not trimmed, so each must match exactly; repeated labels are removed.

### Responses

| Model         | Fields                                                                                          | Returned by                      |
| ------------- | ----------------------------------------------------------------------------------------------- | -------------------------------- |
| `PostSummary` | `id`, `title`, `summary`, `published_on`, `author`                                              | `GET /api/blog`                  |
| `PostDetail`  | The `PostSummary` fields, plus `body`, `updated_at`, `categories`, `tags`, `minutes_to_read`    | `GET /api/blog/{post_id}`, `POST`, `PUT` |

- **`author`:** `{ id, full_name }`.
- **`categories` and `tags`:** lists of `{ id, label }`.
- **`updated_at`:** set by the server on create and update; ISO 8601 in UTC, for example `2025-06-13T15:27:28Z`.

<br>

## Rules behind the contract

- **`422` comes from FastAPI:** Pydantic checks the request body and the `post_id` before the handler runs. A missing field, an empty title, a wrong type, broken JSON, or a post id that is not a whole number from 1 to 2147483647 (the largest PostgreSQL `integer`) all return `422`. No handler code is needed.
- **`401` comes first:** FastAPI runs the session dependency before it checks the body, so a write without a session is a `401` even with an invalid body. The one exception is broken JSON, which is a `422`.
- **`404` comes from the handler:** the handler raises `HTTPException(status_code=404, detail="Post not found")` when no post has the id.
- **`minutes_to_read` is temporary:** in Stages 1 and 2, a plain function calculates it from `body` (200 words per minute, at least 1). In Stage 3, the frontend takes it over, and the field and the function are removed.
- **Empty list is `200`:** `GET /api/blog` with no posts returns `[]`. The collection exists; it is just empty. `404` would mean the path itself is wrong.
- **`PUT`, not `PATCH`:** `PUT` replaces the whole post, so it takes the same `PostInput` body as `POST`. It keeps the original author. `PATCH` would change only the fields sent, which needs merging logic; it can be added later.
