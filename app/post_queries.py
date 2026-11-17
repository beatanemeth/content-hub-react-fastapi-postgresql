"""
The SQL of the post routes.

Each function takes the request's connection and returns models, ids or None.
None or False means "no row": the route decides which HTTP status that is.
Transactions stay in the routes, because a route decides which statements
belong together.
"""

from typing import Literal, cast

import asyncpg

from app.models import PostDetail, PostInput, PostSummary, minutes_to_read

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


async def list_posts(db: asyncpg.Connection) -> list[PostSummary]:
    """Return all posts, newest first."""
    rows = await db.fetch(SELECT_POST_LIST)
    return [PostSummary(**dict(row)) for row in rows]


async def find_post_detail(db: asyncpg.Connection, post_id: int) -> PostDetail | None:
    """Return one post with its author, categories and tags, or None."""
    row = await db.fetchrow(SELECT_POST_DETAIL, post_id)
    if row is None:
        return None
    # minutes_to_read is calculated in Python, not in SQL.
    return PostDetail(**dict(row), minutes_to_read=minutes_to_read(row["body"]))


async def find_ids(
    db: asyncpg.Connection, table: Literal["category", "tag"], labels: list[str]
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


async def insert_post(
    db: asyncpg.Connection, post_input: PostInput, author_id: int
) -> int:
    """Insert the post row and return its new id."""
    # RETURNING id gives back the id PostgreSQL just created. An INSERT always
    # returns its row, so the None in fetchval's type cannot happen.
    return cast(
        int,
        await db.fetchval(
            """INSERT INTO post
                   (title, summary, body, author_id, published_on, updated_at)
               VALUES ($1, $2, $3, $4, $5, now())
               RETURNING id""",
            post_input.title,
            post_input.summary,
            post_input.body,
            author_id,
            post_input.published_on,
        ),
    )


async def update_post(
    db: asyncpg.Connection, post_id: int, post_input: PostInput
) -> bool:
    """Replace the post row; return False if no post has this id."""
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
    return updated is not None


async def delete_post(db: asyncpg.Connection, post_id: int) -> bool:
    """Delete the post; return False if no post has this id."""
    # ON DELETE CASCADE removes the link rows too.
    deleted = await db.fetchval("DELETE FROM post WHERE id = $1 RETURNING id", post_id)
    return deleted is not None


async def insert_links(
    db: asyncpg.Connection, post_id: int, category_ids: list[int], tag_ids: list[int]
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


async def delete_links(db: asyncpg.Connection, post_id: int) -> None:
    """Delete the link rows of a post; PUT then inserts the new ones."""
    await db.execute("DELETE FROM post_category WHERE post_id = $1", post_id)
    await db.execute("DELETE FROM post_tag WHERE post_id = $1", post_id)
