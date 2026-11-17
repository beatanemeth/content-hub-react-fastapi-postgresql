"""
The read-only lists: the staff, and the two checkbox groups of the post form.

Paths here are relative to where main.py mounts the router (/api).
"""

from fastapi import APIRouter

from app.posts_data import CATEGORIES, STAFF, TAGS, Author, Label

option_router = APIRouter(tags=["options"])


@option_router.get("/authors")
async def list_authors() -> list[Author]:
    """List the staff: the only people who can sign in and write posts. Public."""
    return STAFF


@option_router.get("/categories")
async def list_categories() -> list[Label]:
    """List the post categories. Public."""
    return CATEGORIES


@option_router.get("/tags")
async def list_tags() -> list[Label]:
    """List the post tags. Public."""
    return TAGS
