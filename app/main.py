from fastapi import FastAPI

from app import mock_session
from app.options import option_router
from app.post_routes import post_router

app = FastAPI(title="Content Hub API")
app.include_router(post_router, prefix="/api/blog")
app.include_router(mock_session.router)
app.include_router(option_router, prefix="/api")
