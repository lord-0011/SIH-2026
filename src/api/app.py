"""FastAPI Application Entry Point for PAIMANA Backend."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import settings
from src.api.repository import repository
from src.api.routes import meta, ministries, national, projects, sectors, watchlist

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("paimana.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager to load precomputed tables into memory on startup."""
    log.info("Loading precomputed parquet datasets into memory...")
    repository.load_data()
    log.info(
        "PAIMANA DataRepository initialized: %d rows across %d months (latest: %s)",
        len(repository.df),
        len(repository.months_list),
        repository.latest_month,
    )
    yield
    log.info("Shutting down PAIMANA API service.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Read-only serving layer for PAIMANA infrastructure delay risk scores, "
            "causal early-warning indicators, and portfolio intelligence. "
            "Serves precomputed pipeline tables with zero request-time recomputation."
        ),
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount Routers
    app.include_router(meta.router)
    app.include_router(national.router)
    app.include_router(sectors.router)
    app.include_router(ministries.router)
    app.include_router(projects.router)
    app.include_router(watchlist.router)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
