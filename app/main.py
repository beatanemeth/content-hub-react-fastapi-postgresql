from fastapi import FastAPI

from app import mock_session

app = FastAPI(title="Content Hub API")
app.include_router(mock_session.router)
