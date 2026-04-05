import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock

from src.domain.models.base import Base
from src.domain.models.job import Job, JobStatus


@pytest.fixture
def integration_env(mocker):
    """Returns (client, SessionLocal, mock_slack, executor) to test the entire e2e flow."""
    from src.api.main import create_app
    from src.api import dependencies
    from src.infrastructure.plugin_loader import PluginLoader
    from src.domain.services.message_service import MessageService
    from src.domain.services.job_service import JobService
    from src.worker.executor import WorkerExecutor
    from concurrent.futures import Future

    # Setup database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    # Real PluginLoader that scans PATH
    loader = PluginLoader()
    loader.load_from_path()

    # SlackClient is mocked
    mock_slack = MagicMock()

    app = create_app()

    db_instance = SessionLocal()

    def override_db():
        yield db_instance

    def override_message_service():
        return MessageService(db=db_instance, slack_client=mock_slack, plugin_loader=loader)

    app.dependency_overrides[dependencies.get_db] = override_db
    app.dependency_overrides[dependencies.get_message_service] = override_message_service

    client = TestClient(app)

    job_service = JobService(
        db=db_instance,
        max_concurrency=4,
        max_retry_count=3,
        retry_delay_seconds=60,
        slack_client=mock_slack,
    )
    
    # Use sync pool for tests
    original_init = __import__(
        "concurrent.futures", fromlist=["ThreadPoolExecutor"]
    ).ThreadPoolExecutor.__init__

    class _SyncPool:
        def __init__(self, max_workers=None):
            pass

        def submit(self, fn, *args, **kwargs):
            f = Future()
            f.set_running_or_notify_cancel()
            try:
                f.set_result(fn(*args, **kwargs))
            except Exception as exc:
                f.set_exception(exc)
            return f

        def shutdown(self, wait=True):
            pass

    mocker.patch("src.worker.executor.ThreadPoolExecutor", _SyncPool)
    
    executor = WorkerExecutor(
        job_service=job_service,
        plugin_loader=loader,
        slack_client=mock_slack,
        max_workers=1,
        command_timeout=5,
    )

    yield client, SessionLocal, mock_slack, executor

    Base.metadata.drop_all(engine)
    db_instance.close()


class TestCommandFlowIntegration:
    def test_full_command_flow(self, integration_env):
        client, Session, slack, executor = integration_env

        # 1. API receives message
        resp = client.post(
            "/messages",
            json={
                "channel_id": "C123",
                "thread_ts": "111.000",
                "user": "U1",
                "text": "!alert --host web01",
                "timestamp": "111.000",
            },
        )
        assert resp.status_code == 200

        # Verify job is created
        db = Session()
        jobs = db.query(Job).all()
        assert len(jobs) == 1
        assert jobs[0].status == JobStatus.pending
        db.close()

        # 2. Worker executes job
        executor.run_once()  # Picks up the job and starts sync_pool execution
        # 3. Second run_once recovers the done Future
        executor.run_once()

        # Verify job is done
        db = Session()
        jobs = db.query(Job).all()
        assert jobs[0].status == JobStatus.done
        db.close()

        # 4. Verify Slack was notified with the expected result
        slack.post_message.assert_called_once()
        expected_text = "Alert for web01" # actual shell command output value for "result" key
        assert expected_text in slack.post_message.call_args[1]["text"]
