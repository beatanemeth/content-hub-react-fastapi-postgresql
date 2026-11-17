"""
The post routes, with the posts in memory.

Paths here are relative to where main.py mounts the router (/api/blog).
"""

from fastapi import APIRouter

from app.posts_data import PostSummary, newest_first, posts, to_summary

post_router = APIRouter(tags=["blog"])


@post_router.get("")
async def list_all_posts() -> list[PostSummary]:
    """List all posts, newest first. Public. 200, [] when there are none."""
    # sorted() returns a new list, so the stored order does not change.
    return [to_summary(post) for post in sorted(posts, key=newest_first, reverse=True)]
