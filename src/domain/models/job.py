import enum
from datetime import datetime, UTC

from sqlalchemy import DateTime, Enum as SAEnum, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class JobStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    command: Mapped[str] = mapped_column(String(255), nullable=False)
    args: Mapped[str | None] = mapped_column(Text, nullable=True)
    thread_context: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus), default=JobStatus.pending, nullable=False
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_after: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
