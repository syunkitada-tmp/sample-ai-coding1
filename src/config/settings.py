from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "mysql+pymysql://root:password@localhost:3306/chatops"
    slack_proxy_url: str = "http://localhost:8081/post"
    worker_polling_interval: int = 5
    worker_max_concurrency: int = 4
    worker_max_retry_count: int = 3
    worker_retry_delay_seconds: int = 60
    plugin_command_timeout: int = 30
    plugin_command_path: str | None = None


settings = Settings()
