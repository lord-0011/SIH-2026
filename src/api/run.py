"""Stage: api — PAIMANA Read-Only FastAPI Serving Layer.

Entry point: run(config). Reads processed parquets, serves endpoints with zero recomputation.
Governed by docs/steps/STEP_13_api.md.
"""

from __future__ import annotations

from typing import Any

import uvicorn

from src.api.config import settings
from src.common.logging_setup import get_logger

log = get_logger("api")


def run(config: dict[str, Any] | None = None) -> None:
    """Launch the PAIMANA Backend API server using Uvicorn."""
    cfg = config or {}
    host = cfg.get("host", settings.HOST)
    port = int(cfg.get("port", settings.PORT))
    reload = cfg.get("reload", False)

    log.info("Starting PAIMANA API server on http://%s:%d", host, port)
    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    run()
