"""
The in-memory "database": the same rows as the seed files of the database.

Everything lives in memory, so it resets on every server restart.
"""

from pydantic import BaseModel

# The largest value of a PostgreSQL integer column; a bigger id would fail the query.
MAX_DB_INTEGER = 2_147_483_647


class Author(BaseModel):
    id: int
    full_name: str


# staff.csv: the only people who can log in and write posts.
STAFF: list[Author] = [
    Author(id=1, full_name="Martha Lindley"),
    Author(id=2, full_name="Dr. Iris Carter"),
    Author(id=3, full_name="Nora Hall"),
    Author(id=4, full_name="Rose Dalton"),
    Author(id=5, full_name="Leah Bradley"),
    Author(id=6, full_name="Daniel Brooks"),
    Author(id=7, full_name="Peter Hayes"),
    Author(id=8, full_name="Ellie Dean"),
    Author(id=9, full_name="Andrew Fletcher"),
]

STAFF_BY_ID: dict[int, Author] = {person.id: person for person in STAFF}
