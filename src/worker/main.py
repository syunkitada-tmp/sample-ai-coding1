"""ワーカープロセスのエントリポイント。

settings.worker_polling_interval 秒ごとに run_once() を呼び出すポーリングループ。
"""

from __future__ import annotations

import logging
import time

from src.config import settings
from src.infrastructure.db import get_db
from src.infrastructure.plugin_loader import PluginLoader
from src.infrastructure.slack_client import SlackClient
from src.domain.services.job_service import JobService
from src.plugins.help import HelpPlugin
from src.worker.executor import WorkerExecutor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _build_executor() -> WorkerExecutor:
    db = next(get_db())
    slack_client = SlackClient(proxy_url=settings.slack_proxy_url)
    plugin_loader = PluginLoader()
    plugin_loader.load_from_dir(settings.plugin_dir)
    plugin_loader._registry["help"] = HelpPlugin(plugin_loader=plugin_loader)

    job_service = JobService(
        db=db,
        max_concurrency=settings.worker_max_concurrency,
        max_retry_count=settings.worker_max_retry_count,
        retry_delay_seconds=settings.worker_retry_delay_seconds,
        slack_client=slack_client,
    )
    return WorkerExecutor(
        job_service=job_service,
        plugin_loader=plugin_loader,
        slack_client=slack_client,
        max_workers=settings.worker_max_concurrency,
    )


def run() -> None:
    logger.info(
        "Worker started. polling_interval=%ds max_concurrency=%d",
        settings.worker_polling_interval,
        settings.worker_max_concurrency,
    )
    executor = _build_executor()
    try:
        while True:
            try:
                executor.run_once()
            except Exception as exc:
                logger.error("Unexpected error in run_once: %s", exc, exc_info=True)
            time.sleep(settings.worker_polling_interval)
    except KeyboardInterrupt:
        logger.info("Worker shutting down...")
        executor.shutdown()


if __name__ == "__main__":
    run()
