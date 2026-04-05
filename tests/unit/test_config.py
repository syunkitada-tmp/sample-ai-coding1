def test_settings_default_values(monkeypatch):
    monkeypatch.delenv("WORKER_POLLING_INTERVAL", raising=False)
    monkeypatch.delenv("WORKER_MAX_CONCURRENCY", raising=False)
    monkeypatch.delenv("WORKER_MAX_RETRY_COUNT", raising=False)
    monkeypatch.delenv("PLUGIN_COMMAND_TIMEOUT", raising=False)
    monkeypatch.delenv("PLUGIN_COMMAND_PATH", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SLACK_PROXY_URL", "http://localhost:8081/post")

    from src.config import Settings

    s = Settings()
    assert s.worker_polling_interval == 5
    assert s.worker_max_concurrency == 4
    assert s.worker_max_retry_count == 3
    assert s.plugin_command_timeout == 30
    assert s.plugin_command_path is None


def test_settings_custom_values(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://root:test@db/chatops")
    monkeypatch.setenv("SLACK_PROXY_URL", "http://proxy/post")
    monkeypatch.setenv("WORKER_POLLING_INTERVAL", "10")
    monkeypatch.setenv("WORKER_MAX_CONCURRENCY", "8")
    monkeypatch.setenv("WORKER_MAX_RETRY_COUNT", "5")
    monkeypatch.setenv("PLUGIN_COMMAND_TIMEOUT", "60")
    monkeypatch.setenv("PLUGIN_COMMAND_PATH", "/custom/bin")

    from src.config import Settings

    s = Settings()
    assert s.database_url == "mysql+pymysql://root:test@db/chatops"
    assert s.worker_polling_interval == 10
    assert s.worker_max_concurrency == 8
    assert s.worker_max_retry_count == 5
    assert s.plugin_command_timeout == 60
    assert s.plugin_command_path == "/custom/bin"
