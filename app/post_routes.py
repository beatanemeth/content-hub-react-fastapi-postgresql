"""
The post routes, with the posts in memory.

The routes are async def with no await: FastAPI runs them one at a time on the
event loop. A plain def route would run in a thread pool, and two requests could
change the posts list at once.

Paths here are relative to where main.py mounts the router (/api/blog).
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from app.mock_session import CurrentUser, require_user
from app.posts_data import (
    CATEGORIES,
    MAX_DB_INTEGER,
    TAGS,
    Label,
    PostDetail,
    PostInput,
    PostSummary,
    StoredPost,
    newest_first,
    next_post_id,
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


def find_ids(items: list[Label], labels: list[str]) -> tuple[list[int], list[str]]:
    """
    Return the ids of the labels, and every label that is not in the list.

    The in-memory version of SELECT id FROM category WHERE label = ANY($1).
    """
    id_of = {item.label: item.id for item in items}
    unknown = [label for label in labels if label not in id_of]
    return [id_of[label] for label in labels if label in id_of], unknown


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


def label_ids(post_input: PostInput) -> tuple[list[int], list[int]]:
    """Return the category and tag ids of the body's labels; categories first."""
    category_ids, unknown_categories = find_ids(CATEGORIES, post_input.categories)
    raise_if_unknown("category", unknown_categories)

    tag_ids, unknown_tags = find_ids(TAGS, post_input.tags)
    raise_if_unknown("tag", unknown_tags)

    return category_ids, tag_ids


@post_router.get("")
async def list_all_posts() -> list[PostSummary]:
    """List all posts, newest first. Public. 200, [] when there are none."""
    # sorted() returns a new list, so the stored order does not change.
    return [to_summary(post) for post in sorted(posts, key=newest_first, reverse=True)]


@post_router.get("/{post_id}")
async def get_post(post_id: PostId) -> PostDetail:
    """Get one post with author, categories, tags and minutes_to_read. Public."""
    return to_detail(posts[find_index(post_id)])


@post_router.post("", status_code=201)
async def create_post(user: CurrentUser, post_input: PostInput) -> PostDetail:
    """
    Create a post; the author is the signed-in user.

    201, the new post. 400 for an unknown label. 401 'Not signed in'.
    422 for a bad body.
    """
    category_ids, tag_ids = label_ids(post_input)
    post = StoredPost(
        id=next_post_id(),
        title=post_input.title,
        summary=post_input.summary,
        body=post_input.body,
        author_id=user.id,
        published_on=post_input.published_on,
        updated_at=datetime.now(UTC),
        category_ids=category_ids,
        tag_ids=tag_ids,
    )
    posts.append(post)
    return to_detail(post)


# PUT needs a signed-in user but not the user's data (the author never changes),
# so require_user goes in dependencies=[...] instead of a parameter.
# It still runs before the body is checked.
@post_router.put("/{post_id}", dependencies=[Depends(require_user)])
async def replace_post(post_id: PostId, post_input: PostInput) -> PostDetail:
    """
    Replace a post; the author stays the original author.

    200, the updated post. 400 for an unknown label. 401 'Not signed in'.
    404 'Post not found'. 422 for a bad id or body.
    """
    # The labels before the post, as in Stage 2, where only the UPDATE finds out
    # whether the post exists. So PUT /api/blog/999 with an unknown label is a 400.
    category_ids, tag_ids = label_ids(post_input)
    index = find_index(post_id)

    # PUT replaces the post: the id and the author stay; the rest comes from the body.
    posts[index] = StoredPost(
        id=post_id,
        title=post_input.title,
        summary=post_input.summary,
        body=post_input.body,
        author_id=posts[index].author_id,
        published_on=post_input.published_on,
        updated_at=datetime.now(UTC),
        category_ids=category_ids,
        tag_ids=tag_ids,
    )
    return to_detail(posts[index])


@post_router.delete("/{post_id}", status_code=204, dependencies=[Depends(require_user)])
async def remove_post(post_id: PostId) -> None:
    """
    Delete a post.

    204, no body. 401 'Not signed in'. 404 'Post not found'. 422 for a bad id.
    """
    # del changes the list in place, so posts in posts_data.py loses the post too.
    del posts[find_index(post_id)]
