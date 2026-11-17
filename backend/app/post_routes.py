"""
The post routes, with the posts in PostgreSQL.

The SQL is in post_queries.py; here each route turns the query results into
HTTP answers. No try/except around the queries: a failed query raises, and
FastAPI answers 500.

Paths here are relative to where main.py mounts the router (/api/blog).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from app import post_queries
from app.db import DbConnection
from app.mock_session import CurrentUser, require_user
from app.models import MAX_DB_INTEGER, PostDetail, PostInput, PostSummary

# The {post_id} of the URL: a whole number that fits a PostgreSQL integer column.
# 'abc' or 3000000000 is a 422 before the handler runs.
PostId = Annotated[int, Path(ge=1, le=MAX_DB_INTEGER)]

post_router = APIRouter(tags=["blog"])


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
    category_ids, unknown_categories = await post_queries.find_ids(
        db, "category", post_input.categories
    )
    raise_if_unknown("category", unknown_categories)

    tag_ids, unknown_tags = await post_queries.find_ids(db, "tag", post_input.tags)
    raise_if_unknown("tag", unknown_tags)

    return category_ids, tag_ids


@post_router.get("")
async def list_all_posts(db: DbConnection) -> list[PostSummary]:
    """List all posts, newest first. Public. 200, [] when there are none."""
    return await post_queries.list_posts(db)


@post_router.get("/{post_id}")
async def get_post(post_id: PostId, db: DbConnection) -> PostDetail:
    """
    Get one post with author, categories, tags and minutes_to_read. Public.

    Raises
    ------
    HTTPException
        404 if no post has this id.
    """
    post = await post_queries.find_post_detail(db, post_id)
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
        post_id = await post_queries.insert_post(db, post_input, user.id)
        await post_queries.insert_links(db, post_id, category_ids, tag_ids)
        # Read back before COMMIT: if the read fails, the inserts roll back too.
        post = await post_queries.find_post_detail(db, post_id)

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
        # No row was updated: no post has this id. The exception rolls back.
        if not await post_queries.update_post(db, post_id, post_input):
            raise HTTPException(status_code=404, detail="Post not found")

        await post_queries.delete_links(db, post_id)
        await post_queries.insert_links(db, post_id, category_ids, tag_ids)
        # Read back before COMMIT, as in POST: a 500 means "nothing changed".
        post = await post_queries.find_post_detail(db, post_id)

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
    # One statement, so no transaction.
    if not await post_queries.delete_post(db, post_id):
        raise HTTPException(status_code=404, detail="Post not found")
