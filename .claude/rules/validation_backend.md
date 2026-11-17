---
paths:
  - '*.py'
  - 'src/**/*.py'
  - 'backend/**'
---

# Rules: minimal backend validation

- **Pydantic models for request bodies:** every `POST` and `PUT` body is a Pydantic model: `PostInput` for a post, `LoginInput` for the mock login. Pydantic ships with FastAPI, so it is not an extra dependency.
- **Constrained path parameters:** declare the post id as `post_id: PostId`, a whole number from 1 to 2147483647 (the largest PostgreSQL `integer`). FastAPI converts and checks it before the handler runs. A plain `int` lets a bigger number through, and the query then fails with `500`.
- **Constraints as types:** express rules with `Annotated` and `StringConstraints`, `Field` or `AfterValidator`, not with `if` checks in the handler.
- **No hand-written validation:** the handler receives data that is already valid. FastAPI answers invalid input with `422` and a `detail` list; do not add a custom `RequestValidationError` handler.
- **Separate input and output models:** the client sends `PostInput`. The API returns `PostSummary` (in the list) and `PostDetail` (one post), which add the fields the server sets: `id`, `author`, `updated_at`, `minutes_to_read`, and the categories and tags as `{ id, label }`.
- **Labels, not ids; no author:** the body carries category and tag labels. The author comes from the mock session. A field the model does not name, such as `author_id`, is ignored.
- **Existence is not a Pydantic rule:** the handler looks up the labels (in the in-memory lists in Phase 1, with a query from Phase 2) and answers `400` with every unknown label, for example `Unknown category: NoSuchCategory, AlsoMissing`. The `NOT NULL`, `UNIQUE` and foreign key constraints stay in the database.

<br>

## Example: the `PostInput` model and `PostId`

```python
from datetime import date
from typing import Annotated

from fastapi import Path
from pydantic import AfterValidator, BaseModel, Field, StringConstraints

# The largest value of a PostgreSQL integer column
MAX_DB_INTEGER = 2_147_483_647

PostId = Annotated[int, Path(ge=1, le=MAX_DB_INTEGER)]


def reject_nul(value: str) -> str:
    if "\x00" in value:
        raise ValueError("must not contain the NUL character")
    return value


def remove_repeats(labels: list[str]) -> list[str]:
    return list(dict.fromkeys(labels))


Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1), AfterValidator(reject_nul)
]
LabelText = Annotated[str, StringConstraints(min_length=1), AfterValidator(reject_nul)]
LabelList = Annotated[list[LabelText], Field(min_length=1), AfterValidator(remove_repeats)]


class PostInput(BaseModel):
    title: Text
    summary: Text
    body: Text
    published_on: date
    categories: LabelList
    tags: LabelList
```

- **`min_length=1` is needed:** a plain `str` accepts `""`. With `strip_whitespace=True`, a title of only spaces is rejected too.
- **Labels are not trimmed:** each label must match a stored label exactly, so `" Inspiring"` is an unknown tag (`400`).
- **No NUL character:** a PostgreSQL `text` column cannot hold `\u0000`. Without `reject_nul`, the query fails with `500`.
- **Repeated labels are removed:** `["A", "A"]` becomes `["A"]`. Otherwise, the second link row breaks the primary key of `post_category` (a `500`). `dict.fromkeys` keeps the order.
- **Lax mode:** by default, Pydantic converts compatible values, so `"5"` becomes `5` for `person_id` at the mock login, but `1.5` is a `422`. This is enough for a local demo.

<br>

## Example: the `422` response

`POST /api/blog` with `"title": ""` returns `422`:

```json
{
	"detail": [
		{
			"type": "string_too_short",
			"loc": ["body", "title"],
			"msg": "String should have at least 1 character",
			"input": "",
			"ctx": { "min_length": 1 }
		}
	]
}
```

`loc` names the failing field, so the client can show which input is wrong. An invalid post id, such as `abc`, `0` or `3000000000`, has `"loc": ["path", "post_id"]`.
