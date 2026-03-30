from src.domain.models.job import Job, JobStatus


def test_job_default_status(db_session):
    job = Job(
        command="alert",
        args="--host web01",
        thread_context={"channel_id": "C123", "thread_ts": "1234567890.000100"},
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    assert job.id is not None
    assert job.status == JobStatus.pending
    assert job.retry_count == 0
    assert job.retry_after is None
    assert job.failure_reason is None


def test_job_thread_context_stored(db_session):
    ctx = {"channel_id": "C123", "thread_ts": "999.000", "user": "U456"}
    job = Job(
        command="alert",
        thread_context=ctx,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    assert job.thread_context["channel_id"] == "C123"
    assert job.thread_context["thread_ts"] == "999.000"


def test_job_status_enum_values():
    assert JobStatus.pending == "pending"
    assert JobStatus.processing == "processing"
    assert JobStatus.done == "done"
    assert JobStatus.failed == "failed"


def test_job_status_update(db_session):
    job = Job(
        command="alert",
        thread_context={"channel_id": "C123", "thread_ts": "999.000"},
    )
    db_session.add(job)
    db_session.commit()

    job.status = JobStatus.processing
    db_session.commit()
    db_session.refresh(job)
    assert job.status == JobStatus.processing
