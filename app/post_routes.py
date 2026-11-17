"""
The post routes, with the posts in memory.

Paths here are relative to where main.py mounts the router (/api/blog).
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from app.posts_data import (
    MAX_DB_INTEGER,
    PostDetail,
    PostSummary,
    newest_first,
    posts,
    to_detail,
    to_summary,
)

# The {post_id} of the URL: a whole number that fits a PostgreSQL integer column.
# 'abc' or 3000000000 is a 422 before the handler runs.
PostId = Annotated[int, Path(ge=1, le=MAX_DB_INTEGER)]

post_router = APIRouter(tags=["blog"])


def find_index(post_id: int) -> int:
    """
    Return the position of the post in the list.

    Raises
    ------
    HTTPException
        404 if no post has this id.
    """
    for index, post in enumerate(posts):
        if post.id == post_id:
            return index
    raise HTTPException(status_code=404, detail="Post not found")


@post_router.get("")
async def list_all_posts() -> list[PostSummary]:
    """List all posts, newest first. Public. 200, [] when there are none."""
    # sorted() returns a new list, so the stored order does not change.
    return [to_summary(post) for post in sorted(posts, key=newest_first, reverse=True)]


@post_router.get("/{post_id}")
async def get_post(post_id: PostId) -> PostDetail:
    """Get one post with author, categories, tags and minutes_to_read. Public."""
    return to_detail(posts[find_index(post_id)])
