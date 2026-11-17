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


class Label(BaseModel):
    """A category or a tag: both tables have the same two columns."""

    id: int
    label: str


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

# category.csv
CATEGORIES: list[Label] = [
    Label(id=1, label="SavorTheMoment"),
    Label(id=2, label="TasteCloser"),
    Label(id=3, label="CoffeeStories"),
    Label(id=4, label="BeanScience"),
    Label(id=5, label="BeanBanter"),
    Label(id=6, label="FlavourMemory"),
    Label(id=7, label="FromTheCuppingTable"),
    Label(id=8, label="FreshStart"),
]

# tag.csv
TAGS: list[Label] = [
    Label(id=1, label="Inspiring"),
    Label(id=2, label="BrewItDifferently"),
    Label(id=3, label="EverydayRitual"),
    Label(id=4, label="Hospitality"),
    Label(id=5, label="BetterTogether"),
    Label(id=6, label="JustOneCup"),
    Label(id=7, label="BloomAndBurr"),
    Label(id=8, label="AgainstTheGrain"),
    Label(id=9, label="RoastScience"),
    Label(id=10, label="FlavourImagination"),
    Label(id=11, label="WhoSetsTheRules"),
    Label(id=12, label="SpecialityCoffee"),
    Label(id=13, label="EspressoAndExtraction"),
    Label(id=14, label="TasteTraining"),
    Label(id=15, label="WhosTheExpert"),
    Label(id=16, label="CoffeeMyths"),
    Label(id=17, label="MeetTheRoaster"),
]
