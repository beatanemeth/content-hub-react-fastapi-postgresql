from fastapi import FastAPI

from app import mock_session
from app.options import option_router

app = FastAPI(title="Content Hub API")
app.include_router(mock_session.router)
app.include_router(option_router, prefix="/api")
