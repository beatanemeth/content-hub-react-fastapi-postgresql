from pathlib import Path

from asyncpg.exceptions import IntegrityConstraintViolationError
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import mock_session
from app.db import lifespan
from app.options import option_router
from app.post_routes import post_router

# SQLSTATE codes: https://www.postgresql.org/docs/current/errcodes-appendix.html
PG_ERROR_RESPONSE: dict[str, tuple[int, str]] = {
    "23503": (422, "Author, category or tag not found"),  # foreign_key_violation
    "23505": (422, "Duplicate category or tag id"),  # unique_violation
}

# The React build (npm run build); the image keeps the same path relative to this file
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

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


# In development, Vite serves the frontend and dist/ may not exist
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    # Registered last: every route above matches first
    @app.get("/{path:path}", include_in_schema=False)
    async def serve_frontend(path: str) -> FileResponse:
        """
        Return a file from the React build, or index.html for a client-side route.

        Raises
        ------
        HTTPException
            404 for an unknown ``/api`` path, so it stays a JSON error.
        """
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404)
        file = (FRONTEND_DIST / path).resolve()
        # is_relative_to blocks paths such as ../../.env that leave dist/
        if file.is_file() and file.is_relative_to(FRONTEND_DIST):
            return FileResponse(file)
        return FileResponse(FRONTEND_DIST / "index.html")
