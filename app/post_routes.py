"""
The post routes, with the posts in PostgreSQL.

Every route takes the request's connection as a DbConnection parameter. No
try/except around the queries: a failed query raises, and FastAPI answers 500.

Paths here are relative to where main.py mounts the router (/api/blog).
"""

from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Path

from app.db import DbConnection
from app.mock_session import CurrentUser, require_user
from app.posts_data import (
    MAX_DB_INTEGER,
    PostDetail,
    PostInput,
    PostSummary,
    minutes_to_read,
)

# The {post_id} of the URL: a whole number that fits a PostgreSQL integer column.
# 'abc' or 3000000000 is a 422 before the handler runs.
PostId = Annotated[int, Path(ge=1, le=MAX_DB_INTEGER)]

# json_build_object turns the author's two columns into one { id, full_name }
# object; the JSON codec of db.py decodes it into a dict.
AUTHOR = "json_build_object('id', person.id, 'full_name', person.full_name) AS author"

# Only the columns the listing page needs, newest first; the id orders posts
# of the same day.
SELECT_POST_LIST = f"""
    SELECT post.id, post.title, post.summary, post.published_on, {AUTHOR}
    FROM post
    JOIN person ON person.id = post.author_id
    ORDER BY post.published_on DESC, post.id DESC
"""

# One post, and the answer to POST and PUT. Each subquery collects the post's
# link rows into a JSON list of { id, label }; json_agg gives NULL when there
# are no rows, and COALESCE turns that into [].
SELECT_POST_DETAIL = f"""
    SELECT post.id, post.title, post.summary, post.body, post.published_on,
        post.updated_at, {AUTHOR},
        COALESCE(
            (SELECT json_agg(
                        json_build_object('id', category.id, 'label', category.label)
                        ORDER BY category.id)
             FROM post_category
             JOIN category ON category.id = post_category.category_id
             WHERE post_category.post_id = post.id),
            '[]'
        ) AS categories,
        COALESCE(
            (SELECT json_agg(
                        json_build_object('id', tag.id, 'label', tag.label)
                        ORDER BY tag.id)
             FROM post_tag
             JOIN tag ON tag.id = post_tag.tag_id
             WHERE post_tag.post_id = post.id),
            '[]'
        ) AS tags
    FROM post
    JOIN person ON person.id = post.author_id
    WHERE post.id = $1
"""

post_router = APIRouter(tags=["blog"])


async def find_ids(
    db: DbConnection, table: Literal["category", "tag"], labels: list[str]
) -> tuple[list[int], list[str]]:
    """
    Return the ids of the labels, and every label that has no row.

    The table name cannot be a $ placeholder, so it goes into the SQL text. That
    is safe only because the type allows just these two fixed names.
    """
    # = ANY($1) matches any item of the array; asyncpg sends the list as text[].
    rows = await db.fetch(
        f"SELECT id, label FROM {table} WHERE label = ANY($1::text[])", labels
    )
    found = {row["label"] for row in rows}
    unknown = [label for label in labels if label not in found]
    return [row["id"] for row in rows], unknown


def raise_if_unknown(kind: str, unknown: list[str]) -> None:
    """
    Name every label with no row, for example 'Unknown category: NoSuch, AlsoMissing'.

    Raises
    ------
    HTTPException
        400 if any label is unknown.
    """
    if unknown:
        raise HTTPException(
            status_code=400, detail=f"Unknown {kind}: {', '.join(unknown)}"
        )


async def label_ids(
    db: DbConnection, post_input: PostInput
) -> tuple[list[int], list[int]]:
    """Return the category and tag ids of the body's labels; categories first."""
    category_ids, unknown_categories = await find_ids(
        db, "category", post_input.categories
    )
    raise_if_unknown("category", unknown_categories)

    tag_ids, unknown_tags = await find_ids(db, "tag", post_input.tags)
    raise_if_unknown("tag", unknown_tags)

    return category_ids, tag_ids


async def find_post_detail(db: DbConnection, post_id: int) -> PostDetail | None:
    """Return one post with its author, categories and tags, or None."""
    row = await db.fetchrow(SELECT_POST_DETAIL, post_id)
    if row is None:
        return None
    # minutes_to_read is calculated in Python, not in SQL.
    return PostDetail(**dict(row), minutes_to_read=minutes_to_read(row["body"]))


async def insert_links(
    db: DbConnection, post_id: int, category_ids: list[int], tag_ids: list[int]
) -> None:
    """
    Insert the link rows of a post, one statement per table.

    unnest turns the list into rows: [4, 6] becomes (post_id, 4) and (post_id, 6).
    """
    await db.execute(
        "INSERT INTO post_category (post_id, category_id) SELECT $1, unnest($2::int[])",
        post_id,
        category_ids,
    )
    await db.execute(
        "INSERT INTO post_tag (post_id, tag_id) SELECT $1, unnest($2::int[])",
        post_id,
        tag_ids,
    )


async def delete_links(db: DbConnection, post_id: int) -> None:
    """Delete the link rows of a post; PUT then inserts the new ones."""
    await db.execute("DELETE FROM post_category WHERE post_id = $1", post_id)
    await db.execute("DELETE FROM post_tag WHERE post_id = $1", post_id)


@post_router.get("")
async def list_all_posts(db: DbConnection) -> list[PostSummary]:
    """List all posts, newest first. Public. 200, [] when there are none."""
    rows = await db.fetch(SELECT_POST_LIST)
    return [PostSummary(**dict(row)) for row in rows]


@post_router.get("/{post_id}")
async def get_post(post_id: PostId, db: DbConnection) -> PostDetail:
    """
    Get one post with author, categories, tags and minutes_to_read. Public.

    Raises
    ------
    HTTPException
        404 if no post has this id.
    """
    post = await find_post_detail(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@post_router.post("", status_code=201)
async def create_post(
    user: CurrentUser, post_input: PostInput, db: DbConnection
) -> PostDetail:
    """
    Create a post; the author is the signed-in user.

    201, the new post. 400 for an unknown label. 401 'Not signed in'.
    422 for a bad body.
    """
    # Outside the transaction: it only reads.
    category_ids, tag_ids = await label_ids(db, post_input)

    # BEGIN here; COMMIT when the block ends normally, ROLLBACK when an exception
    # leaves it. The whole request uses one connection, so both run on the same one.
    async with db.transaction():
        # RETURNING id gives back the id PostgreSQL just created. An INSERT
        # always returns its row, so the None in fetchval's type cannot happen.
        post_id = cast(
            int,
            await db.fetchval(
                """INSERT INTO post
                       (title, summary, body, author_id, published_on, updated_at)
                   VALUES ($1, $2, $3, $4, $5, now())
                   RETURNING id""",
                post_input.title,
                post_input.summary,
                post_input.body,
                user.id,
                post_input.published_on,
            ),
        )
        await insert_links(db, post_id, category_ids, tag_ids)
        # Read back before COMMIT: if the read fails, the inserts roll back too.
        post = await find_post_detail(db, post_id)

    if post is None:
        raise RuntimeError("The new post was not found after the INSERT")
    return post


# PUT needs a signed-in user but not the user's data (the author never changes),
# so require_user goes in dependencies=[...] instead of a parameter.
# It still runs before the body is checked.
@post_router.put("/{post_id}", dependencies=[Depends(require_user)])
async def replace_post(
    post_id: PostId, post_input: PostInput, db: DbConnection
) -> PostDetail:
    """
    Replace a post; the author stays the original author.

    200, the updated post. 400 for an unknown label. 401 'Not signed in'.
    404 'Post not found'. 422 for a bad id or body.

    Raises
    ------
    HTTPException
        400 if a label is unknown; 404 if no post has this id.
    """
    # The labels before the post: only the UPDATE finds out whether the post
    # exists. So PUT /api/blog/999 with an unknown label is a 400.
    category_ids, tag_ids = await label_ids(db, post_input)

    async with db.transaction():
        # PUT replaces the post: id and author_id stay; the rest comes from the body.
        updated = await db.fetchval(
            """UPDATE post
               SET title = $1, summary = $2, body = $3, published_on = $4,
                   updated_at = now()
               WHERE id = $5
               RETURNING id""",
            post_input.title,
            post_input.summary,
            post_input.body,
            post_input.published_on,
            post_id,
        )
        # No row came back: no post has this id. The exception rolls back.
        if updated is None:
            raise HTTPException(status_code=404, detail="Post not found")

        await delete_links(db, post_id)
        await insert_links(db, post_id, category_ids, tag_ids)
        # Read back before COMMIT, as in POST: a 500 means "nothing changed".
        post = await find_post_detail(db, post_id)

    if post is None:
        raise RuntimeError("The updated post was not found after the UPDATE")
    return post


@post_router.delete("/{post_id}", status_code=204, dependencies=[Depends(require_user)])
async def remove_post(post_id: PostId, db: DbConnection) -> None:
    """
    Delete a post.

    204, no body. 401 'Not signed in'. 404 'Post not found'. 422 for a bad id.

    Raises
    ------
    HTTPException
        404 if no post has this id.
    """
    # One statement, so no transaction: ON DELETE CASCADE removes the link rows too.
    deleted = await db.fetchval("DELETE FROM post WHERE id = $1 RETURNING id", post_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Post not found")
