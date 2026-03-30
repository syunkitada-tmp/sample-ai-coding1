from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.dependencies import get_message_service
from src.domain.services.message_service import MessageService

router = APIRouter()


class MessageRequest(BaseModel):
    channel_id: str
    thread_ts: str | None = None
    user: str
    text: str
    timestamp: str


@router.post("/messages", status_code=200)
def receive_message(
    body: MessageRequest,
    svc: MessageService = Depends(get_message_service),
) -> dict:
    svc.handle(
        channel_id=body.channel_id,
        thread_ts=body.thread_ts,
        user=body.user,
        text=body.text,
        timestamp=body.timestamp,
    )
    return {"status": "ok"}
