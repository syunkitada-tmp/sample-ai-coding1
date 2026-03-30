def test_settings_default_values(monkeypatch):
    monkeypatch.delenv("WORKER_POLLING_INTERVAL", raising=False)
    monkeypatch.delenv("WORKER_MAX_CONCURRENCY", raising=False)
    monkeypatch.delenv("WORKER_MAX_RETRY_COUNT", raising=False)
    monkeypatch.delenv("PLUGIN_DIR", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SLACK_PROXY_URL", "http://localhost:8081/post")

    from src.config import Settings

    s = Settings()
    assert s.worker_polling_interval == 5
    assert s.worker_max_concurrency == 4
    assert s.worker_max_retry_count == 3
    assert s.plugin_dir == "src/plugins"


def test_settings_custom_values(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://root:test@db/chatops")
    monkeypatch.setenv("SLACK_PROXY_URL", "http://proxy/post")
    monkeypatch.setenv("WORKER_POLLING_INTERVAL", "10")
    monkeypatch.setenv("WORKER_MAX_CONCURRENCY", "8")
    monkeypatch.setenv("WORKER_MAX_RETRY_COUNT", "5")
    monkeypatch.setenv("PLUGIN_DIR", "custom/plugins")

    from src.config import Settings

    s = Settings()
    assert s.database_url == "mysql+pymysql://root:test@db/chatops"
    assert s.worker_polling_interval == 10
    assert s.worker_max_concurrency == 8
    assert s.worker_max_retry_count == 5
    assert s.plugin_dir == "custom/plugins"
