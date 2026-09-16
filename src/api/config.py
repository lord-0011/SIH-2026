"""Configuration settings for the PAIMANA Backend API."""

from __future__ import annotations

import os
from pathlib import Path


class Settings:
    """API server and data path configuration."""

    PROJECT_NAME: str = "PAIMANA Predictive Monitoring API"
    VERSION: str = "1.0.0"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    HOST: str = API_HOST
    PORT: int = API_PORT
    CORS_ORIGINS: list[str] = ["*"]

    # Processed Parquet Data Paths
    PANEL_PARQUET_PATH: Path = Path(os.getenv("PANEL_PARQUET_PATH", "data/processed/panel.parquet"))
    RISK_SCORES_PARQUET_PATH: Path = Path(
        os.getenv("RISK_SCORES_PARQUET_PATH", "data/processed/risk_scores.parquet")
    )
    EARLY_WARNING_PARQUET_PATH: Path = Path(
        os.getenv("EARLY_WARNING_PARQUET_PATH", "data/processed/early_warning.parquet")
    )
    FEATURES_PARQUET_PATH: Path = Path(
        os.getenv("FEATURES_PARQUET_PATH", "data/processed/features.parquet")
    )


settings = Settings()
