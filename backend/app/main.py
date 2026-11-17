from asyncpg.exceptions import IntegrityConstraintViolationError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import mock_session
from app.db import lifespan
from app.options import option_router
from app.post_routes import post_router

# SQLSTATE codes: https://www.postgresql.org/docs/current/errcodes-appendix.html
PG_ERROR_RESPONSE: dict[str, tuple[int, str]] = {
    "23503": (422, "Author, category or tag not found"),  # foreign_key_violation
    "23505": (422, "Duplicate category or tag id"),  # unique_violation
}

app = FastAPI(title="Content Hub API", lifespan=lifespan)
app.include_router(post_router, prefix="/api/blog")
app.include_router(mock_session.router)
app.include_router(option_router, prefix="/api")


@app.exception_handler(IntegrityConstraintViolationError)
async def integrity_error_handler(
    _request: Request, exc: IntegrityConstraintViolationError
) -> JSONResponse:
    """
    Answer a broken database rule with its status and a detail message.

    Raises
    ------
    IntegrityConstraintViolationError
        Again, for a code not in PG_ERROR_RESPONSE: FastAPI answers 500.
    """
    response = PG_ERROR_RESPONSE.get(exc.sqlstate)
    if response is None:
        raise exc
    status_code, message = response
    return JSONResponse(status_code=status_code, content={"detail": message})
