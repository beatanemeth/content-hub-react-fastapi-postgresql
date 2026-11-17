"""
The read-only lists: the staff, and the two checkbox groups of the post form.

Paths here are relative to where main.py mounts the router (/api).
"""

from fastapi import APIRouter

from app.db import DbConnection
from app.models import Author, Label

option_router = APIRouter(tags=["options"])


@option_router.get("/authors")
async def list_authors(db: DbConnection) -> list[Author]:
    """List the staff: the only people who can sign in and write posts. Public."""
    # JOIN staff keeps only the persons who have a staff row.
    rows = await db.fetch(
        """SELECT person.id, person.full_name
           FROM person
           JOIN staff ON staff.person_id = person.id
           ORDER BY person.id"""
    )
    return [Author(**dict(row)) for row in rows]


@option_router.get("/categories")
async def list_categories(db: DbConnection) -> list[Label]:
    """List the post categories. Public."""
    rows = await db.fetch("SELECT id, label FROM category ORDER BY id")
    return [Label(**dict(row)) for row in rows]


@option_router.get("/tags")
async def list_tags(db: DbConnection) -> list[Label]:
    """List the post tags. Public."""
    rows = await db.fetch("SELECT id, label FROM tag ORDER BY id")
    return [Label(**dict(row)) for row in rows]
