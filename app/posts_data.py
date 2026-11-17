"""
The in-memory "database": the same rows as the seed files of the database.

Everything lives in memory, so it resets on every server restart.
"""

# The post texts are long single strings, as in post.csv; Ruff cannot wrap them.
# ruff: noqa: E501

from dataclasses import dataclass
from datetime import date, datetime

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


class PostSummary(BaseModel):
    """One item of GET /api/blog: what the listing page shows, plus the id for the link."""

    id: int
    title: str
    summary: str
    published_on: date  # written as '2020-12-28'
    author: Author


@dataclass
class StoredPost:
    """A post as stored: the post row plus the ids from post_category and post_tag."""

    id: int
    title: str
    summary: str
    body: str
    author_id: int
    published_on: date
    updated_at: datetime
    category_ids: list[int]
    tag_ids: list[int]


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

# The first 3 rows of post.csv, with their rows from post_category.csv and post_tag.csv.
posts: list[StoredPost] = [
    StoredPost(
        id=1,
        title="The 8 Secrets of the 8-Step Espresso Routine",
        summary="Eight simple steps, done the same way every time. Here's the espresso routine we teach at our clinics – and the secret behind each step.",
        body="At our espresso clinics, we teach a simple eight-step routine. It isn't the only way to make espresso, but it's consistent, easy to remember and works on almost any machine. Here are the steps, and the secret behind each one. 1. Purge the group head. Run a little water through before you start. Secret: it stabilises temperature and rinses away old coffee. 2. Dry the basket. Wipe the portafilter clean and dry. Secret: water in the basket leads to uneven extraction. 3. Weigh your dose. Use a scale every time. Secret: half a gram can change the taste noticeably. 4. Distribute the grounds. Tap or use a tool to level the bed. Secret: even distribution prevents channelling. 5. Tamp level. Press firmly and evenly. Secret: a level tamp matters far more than how hard you press. 6. Lock in and start immediately. Don't let the portafilter sit in the hot group. Secret: waiting can scorch the top of the puck. 7. Watch and time the shot. Note the time and the yield. Secret: consistency comes from measuring, not guessing. 8. Taste and adjust. Sour? Grind finer. Bitter? Grind coarser. Secret: change only one thing at a time. That's it. Eight steps, done the same way, every time. The real secret is not any single step, but the routine itself. When the process is consistent, you can finally taste what your adjustments are doing. Practise it daily for two weeks and it will feel natural. Your espresso, and your confidence, will thank you.",
        author_id=6,
        published_on=date(2020, 12, 28),
        updated_at=datetime.fromisoformat("2025-06-13T15:27:28.000Z"),
        category_ids=[4],
        tag_ids=[1],
    ),
    StoredPost(
        id=2,
        title="Change: The Biggest Step Is Step Zero!",
        summary="Before the first step of any change, there's a step most people skip: deciding why you want it. Our series on change continues.",
        body='In this series, we\'ve talked about the stages of change and how to break big goals into small steps. But there\'s one step that comes before all the others, and it\'s the one most people skip. We call it step zero. Step zero is deciding why. Why do you want to change your coffee habit? Not why you think you should, or why someone else wants you to. Why do you want it? This might sound obvious, but it makes an enormous difference. People who start a change without a clear reason often give up when it gets hard. People who know their why are much more likely to keep going. At our clinics, we ask new participants this question. The answers vary widely. "I want my morning coffee to be something I look forward to." "I want to understand what I\'m tasting." "I want to stop spending so much money in cafés." "My partner loves coffee and I want to share that with them." Each of these is a good reason. And each one points to a different path. Someone who wants to save money needs a simple, reliable home setup. Someone who wants to understand tasting needs cupping sessions and side-by-side comparisons. Someone who wants to share a passion with a partner needs a ritual for two. Without step zero, people often choose the wrong path. They buy an expensive espresso machine when what they really wanted was a calm ten minutes in the morning. Then they feel frustrated and give up. So before you take your first step, sit down with a cup of whatever coffee you have now. Ask yourself: what do I really want from this? Write the answer down. Keep it somewhere you\'ll see it. It\'s a small step. In many ways, it\'s the biggest one.',
        author_id=1,
        published_on=date(2021, 1, 5),
        updated_at=datetime.fromisoformat("2025-05-12T13:56:35.000Z"),
        category_ids=[6],
        tag_ids=[2],
    ),
    StoredPost(
        id=3,
        title="Three Days at the Coffee House Retreat",
        summary="Three days in a farmhouse, twenty-four participants and more coffee than we care to admit. Participants share their thoughts from our autumn retreat.",
        body='In September, we held our first three-day Coffee House Retreat at a converted farmhouse in the countryside. Twenty-four participants, four instructors and a kitchen transformed into a brewing lab. We asked participants to share a few thoughts afterwards. "I came for the espresso lessons, but what I\'ll remember is the morning walks with coffee in our hands, watching the mist lift off the fields. I didn\'t know I needed that kind of quiet." – Esther "On the first day, I was too shy to say what I tasted. By the third day, I was arguing passionately that a Colombian tasted like rhubarb. Everyone was so welcoming that I forgot to be nervous." – Dennis "The roasting workshop changed how I see coffee completely. Watching the beans change colour, smelling every stage, I finally understood why freshness matters so much." – Judith "I\'ve been brewing at home for years and thought I knew a lot. This retreat showed me how much more there is to learn, and that learning with others is much more fun than learning alone." – Frank "The evenings were my favourite. Sitting around the long table, sharing food, telling stories, drinking decaf so we could sleep. It felt like a family." – Kate As organisers, we were moved by how quickly the group became close. People arrived as strangers on Friday afternoon. By Sunday, they were exchanging phone numbers, planning visits to each other\'s favourite cafés and promising to meet at the next Cupping Day. We\'ll run the retreat again next year, with a few improvements: more blankets for the cold mornings, and a bigger milk fridge. If you\'d like to join, keep an eye on our newsletter. Thank you to everyone who made these three days so special.',
        author_id=1,
        published_on=date(2021, 9, 24),
        updated_at=datetime.fromisoformat("2025-12-02T13:28:07.000Z"),
        category_ids=[7],
        tag_ids=[1, 3, 5, 7],
    ),
]


def to_summary(post: StoredPost) -> PostSummary:
    """Turn a stored post into a list item: the author id becomes the author."""
    return PostSummary(
        id=post.id,
        title=post.title,
        summary=post.summary,
        published_on=post.published_on,
        author=STAFF_BY_ID[post.author_id],
    )


def newest_first(post: StoredPost) -> tuple[date, int]:
    """Return the sort key of ORDER BY published_on DESC, id DESC, used with reverse=True."""
    return (post.published_on, post.id)
