from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.api.routers import messages


def create_app() -> FastAPI:
    app = FastAPI(title="ChatOps Framework API")
    app.include_router(messages.router)

    @app.get("/health", include_in_schema=False)
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return app


app = create_app()
