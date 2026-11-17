from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, cast

import asyncpg
from fastapi import Depends, FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env also holds the POSTGRES_* keys for Compose; "ignore" skips them
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str


_pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """
    Open the connection pool at start-up and close it at shutdown.

    The code before ``yield`` runs once before the first request; the code after
    it runs once when the server stops.
    """
    global _pool
    # Pyright sees a required argument; pydantic-settings fills it from .env
    settings = Settings()  # pyright: ignore[reportCallIssue]
    _pool = await asyncpg.create_pool(settings.database_url)
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
