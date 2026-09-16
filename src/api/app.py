"""FastAPI Application Factory for PAIMANA Infrastructure Risk Serving Layer (STEP_13).

Integrates all route modules, CORS middleware, and precomputed data repository.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.data_loader import DataLoader
from src.api.routes import health, ministries, national, projects, sectors, watchlist

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to pre-load datasets on startup."""
    log.info("Starting PAIMANA FastAPI application, loading precomputed data...")
    loader = DataLoader.get_instance()
    success = loader.load_data()
    if success:
        log.info("Precomputed data loaded successfully on startup.")
    else:
        log.warning(
            "Precomputed data not loaded on startup (tables may be missing or running in test mode)."
        )
    yield
    log.info("Shutting down PAIMANA FastAPI application.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="PAIMANA — Infrastructure Project Risk Early Warning API",
        description=(
            "FastAPI serving layer for Ministry of Statistics and Programme Implementation (MoSPI) "
            "OCMS infrastructure project monitoring. Provides 3-level dashboard aggregation, "
            "calibrated 0-100 risk scoring, multi-month early warning detection, and project drilldowns."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Enable CORS for React dashboard frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Routers
    app.include_router(health.router)
    app.include_router(national.router)
    app.include_router(sectors.router)
    app.include_router(ministries.router)
    app.include_router(projects.router)
    app.include_router(watchlist.router)

    return app


app = create_app()
