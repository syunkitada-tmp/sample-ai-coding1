from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.routers import messages
from src.lib.logging import configure_logging, set_trace_id


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="ChatOps Framework API")
    app.include_router(messages.router)

    @app.middleware("http")
    async def trace_id_middleware(request: Request, call_next):
        set_trace_id(str(uuid.uuid4()))
        try:
            response = await call_next(request)
        finally:
            set_trace_id(None)
        return response

    @app.get("/health", include_in_schema=False)
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return app


app = create_app()
