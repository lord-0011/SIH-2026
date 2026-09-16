"""Stage runner and server entrypoint for Backend API (STEP_13).

Entry point: run(config). Reads precomputed tables from data/processed.
Runnable via: python -m src.api.run
"""

from __future__ import annotations

import argparse
from typing import Any

import uvicorn

from src.common.logging_setup import get_logger

log = get_logger("api.run")


def run(config: dict[str, Any] | None = None) -> None:
    """Launch the FastAPI Uvicorn web server."""
    cfg = config or {}
    host = cfg.get("host", "127.0.0.1")
    port = int(cfg.get("port", 8000))
    reload = bool(cfg.get("reload", False))

    log.info("Starting PAIMANA Backend API server on http://%s:%d (reload=%s)", host, port, reload)
    uvicorn.run("src.api.app:app", host=host, port=port, reload=reload)


def main() -> None:
    """Parse CLI arguments and launch server."""
    parser = argparse.ArgumentParser(description="PAIMANA Backend API Server")
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host IP to bind (default: 127.0.0.1)"
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    run(vars(args))


if __name__ == "__main__":
    main()
