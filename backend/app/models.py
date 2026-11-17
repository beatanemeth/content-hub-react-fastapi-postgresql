"""
The API's models: what it sends back, and the bodies it reads.

A value that fails its type here never reaches a route: FastAPI answers 422.
"""

import math
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

# The largest value of a PostgreSQL integer column; a bigger id would fail the query.
MAX_DB_INTEGER = 2_147_483_647

# An average adult reading speed for plain text.
WORDS_PER_MINUTE = 200


class Author(BaseModel):
    id: int
    full_name: str


class Label(BaseModel):
    """A category or a tag: both tables have the same two columns."""

    id: int
    label: str


class PostSummary(BaseModel):
    """One item of GET /api/blog: what the listing page shows, and the id."""

    id: int
    title: str
    summary: str
    published_on: date  # written as '2020-12-28'
    author: Author


class PostDetail(PostSummary):
    """GET /api/blog/{post_id}, and the answer to POST and PUT."""

    body: str
    updated_at: datetime  # written in ISO 8601 UTC, for example '2025-06-13T15:27:28Z'
    categories: list[Label]
    tags: list[Label]
    minutes_to_read: int


def reject_nul(value: str) -> str:
    """
    Reject the NUL character (written as u0000 in JSON) with a 422.

    A PostgreSQL text column cannot hold it, so the query would fail (a 500).
    """
    if "\x00" in value:
        raise ValueError("must not contain the NUL character")
    return value


def remove_repeats(labels: list[str]) -> list[str]:
    """Turn ['A', 'A'] into ['A']; a repeat breaks the post_category key."""
    return list(dict.fromkeys(labels))


# Trimmed, then at least one character, and no NUL.
Text = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    AfterValidator(reject_nul),
]
# Not trimmed: a label must match a stored label exactly, so ' Inspiring' is a 400.
LabelText = Annotated[str, StringConstraints(min_length=1), AfterValidator(reject_nul)]
LabelList = Annotated[
    list[LabelText], Field(min_length=1), AfterValidator(remove_repeats)
]


class PostInput(BaseModel):
    """
    The body of POST and PUT, already checked and trimmed.

    Labels, not ids: the backend looks up the ids. No author: it comes from the
    session, and a field the model does not name (author_id, for example) is ignored.
    """

    title: Text
    summary: Text
    body: Text
    published_on: date  # 'YYYY-MM-DD'; an impossible date (2026-02-30) is a 422
    categories: LabelList  # labels, for example ['BeanScience']
    tags: LabelList


def minutes_to_read(body: str) -> int:
    """
    Return the reading time of the body, at least 1 minute.

    Stages 1 and 2 only: in Stage 3, the frontend takes it over.
    """
    return max(1, math.ceil(len(body.split()) / WORDS_PER_MINUTE))
