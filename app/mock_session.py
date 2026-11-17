"""
A stand-in for real sign-in: the mock session and its routes.

Real sign-in later replaces this file; the post routes stay.
"""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, Field

from app.db import DbConnection
from app.posts_data import MAX_DB_INTEGER, Author

COOKIE_NAME = "session_id"


class LoginInput(BaseModel):
    person_id: Annotated[int, Field(ge=1, le=MAX_DB_INTEGER)]


router = APIRouter()

# The mock session store: session id → person id. A server restart empties it.
sessions: dict[str, int] = {}

# For the routes that need a signed-in user; /docs shows them with a lock icon.
# auto_error=False: a missing cookie gives None and the same 401 as an unknown one.
session_scheme = APIKeyCookie(name=COOKIE_NAME, auto_error=False)

# For mock-login and mock-logout, which work with or without a session.
SessionCookie = Annotated[str | None, Cookie(alias=COOKIE_NAME)]


async def find_staff(db: DbConnection, person_id: int) -> Author | None:
    """Return the staff member with this id, or None if the person has no staff row."""
    row = await db.fetchrow(
        """SELECT person.id, person.full_name
           FROM person
           JOIN staff ON staff.person_id = person.id
           WHERE person.id = $1""",
        person_id,
    )
    # An asyncpg Record is not a dict; dict() turns it into one for Pydantic.
    return None if row is None else Author(**dict(row))


async def require_user(
    session_id: Annotated[str | None, Depends(session_scheme)],
    db: DbConnection,
) -> Author:
    """
    Return the signed-in staff member, checked against the staff table.

    Raises
    ------
    HTTPException
        401 if the cookie is missing, its session is unknown, or the person
        is no longer staff.
    """
    person_id = None if session_id is None else sessions.get(session_id)
    person = None if person_id is None else await find_staff(db, person_id)
    if person is None:
        # A staff row removed after login ends the session.
        if session_id is not None:
            sessions.pop(session_id, None)
        raise HTTPException(
            status_code=401,
            detail="Not signed in",
            headers={"WWW-Authenticate": "APIKey"},
        )
    return person


CurrentUser = Annotated[Author, Depends(require_user)]


@router.post(
    "/api/mock-login",
    summary="Log in as a staff member",
    response_model=Author,
    responses={401: {"description": "Unknown staff member"}},
)
async def mock_login(
    login: LoginInput,
    response: Response,
    db: DbConnection,
    old_session_id: SessionCookie = None,
) -> Author:
    """
    Start a session for a staff member and set its cookie. No password: it is a mock.

    Raises
    ------
    HTTPException
        401 if no staff member has this id.
    """
    person = await find_staff(db, login.person_id)
    if person is None:
        raise HTTPException(status_code=401, detail="Unknown staff member")

    # A second login in the same browser replaces the old session.
    if old_session_id is not None:
        sessions.pop(old_session_id, None)
    session_id = str(uuid4())
    sessions[session_id] = person.id

    # httponly: frontend JavaScript cannot read it. samesite="lax": other sites
    # cannot send it with a POST, PUT or DELETE (CSRF protection).
    response.set_cookie(COOKIE_NAME, session_id, httponly=True, samesite="lax")
    return person


@router.post("/api/mock-logout", summary="Log out", status_code=204)
async def mock_logout(response: Response, session_id: SessionCookie = None) -> None:
    """End the session and clear its cookie; harmless without a session."""
    if session_id is not None:
        sessions.pop(session_id, None)
    response.delete_cookie(COOKIE_NAME, httponly=True, samesite="lax")


@router.get(
    "/api/me",
    summary="Show who is logged in",
    response_model=Author,
    responses={401: {"description": "Not signed in"}},
)
async def me(user: CurrentUser) -> Author:
    """
    Return the signed-in staff member.

    Raises
    ------
    HTTPException
        401 if no one is signed in (from require_user).
    """
    return user
