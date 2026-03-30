from __future__ import annotations

from fastapi import FastAPI

from src.api.routers import messages


def create_app() -> FastAPI:
    app = FastAPI(title="ChatOps Framework API")
    app.include_router(messages.router)
    return app


app = create_app()
