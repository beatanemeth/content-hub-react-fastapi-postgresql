import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, cast

import asyncpg
from fastapi import Depends, FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # The server runs from backend/; .env stays in the root, next to docker-compose.yaml
    # .env also holds the POSTGRES_* keys for Compose; "ignore" skips them
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str
    # Only the local .env turns it off, for REST Client over http://localhost
    is_cookie_secure: bool = True


# Read once at import, shared by the pool and the session cookie.
# Pyright sees a required argument; pydantic-settings fills it from .env
settings = Settings()  # pyright: ignore[reportCallIssue]

_pool: asyncpg.Pool | None = None


async def init_connection(connection: asyncpg.Connection) -> None:
    """
    Decode ``json`` columns into Python lists and dicts.

    By default, asyncpg returns a ``json`` value as a string. The pool calls this
    once for each new connection.
    """
    await connection.set_type_codec(
        "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """
    Open the connection pool at start-up and close it at shutdown.

    The code before ``yield`` runs once before the first request; the code after
    it runs once when the server stops.
    """
    global _pool
    _pool = await asyncpg.create_pool(settings.database_url, init=init_connection)
    yield
    await _pool.close()


async def get_connection() -> AsyncIterator[asyncpg.Connection]:
    """
    Lend one pool connection to a request.

    The connection goes back to the pool when the request ends, after a success
    or an error.

    Raises
    ------
    RuntimeError
        If the app was created without ``lifespan``, so the pool is not open.
    """
    if _pool is None:
        raise RuntimeError(
            "The pool is not open: create the app with FastAPI(lifespan=lifespan)"
        )

    async with _pool.acquire() as connection:
        # A proxy that adds Connection's methods at runtime, which Pyright cannot see
        yield cast(asyncpg.Connection, connection)


DbConnection = Annotated[asyncpg.Connection, Depends(get_connection)]
