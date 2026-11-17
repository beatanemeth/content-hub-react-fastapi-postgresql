"""
A stand-in for real sign-in: the mock session and its routes.

Real sign-in later replaces this file; the post routes stay.
"""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, Field

from app.posts_data import MAX_DB_INTEGER, STAFF, STAFF_BY_ID, Author

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


async def require_user(
    session_id: Annotated[str | None, Depends(session_scheme)],
) -> Author:
    """
    Return the signed-in staff member.

    Raises
    ------
    HTTPException
        401 if the cookie is missing or its session is unknown.
    """
    if session_id is None or session_id not in sessions:
        raise HTTPException(
            status_code=401,
            detail="Not signed in",
            headers={"WWW-Authenticate": "APIKey"},
        )
    return STAFF_BY_ID[sessions[session_id]]


CurrentUser = Annotated[Author, Depends(require_user)]


@router.post(
    "/api/mock-login",
    summary="Log in as a staff member",
    response_model=Author,
    responses={401: {"description": "Unknown staff member"}},
)
async def mock_login(
    login: LoginInput, response: Response, old_session_id: SessionCookie = None
) -> Author:
    """
    Start a session for a staff member and set its cookie. No password: it is a mock.

    Raises
    ------
    HTTPException
        401 if no staff member has this id.
    """
    person = STAFF_BY_ID.get(login.person_id)
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


@router.get("/api/authors", summary="List the staff", response_model=list[Author])
async def list_authors() -> list[Author]:
    """Return the staff: the only people who can log in and write posts."""
    return STAFF
