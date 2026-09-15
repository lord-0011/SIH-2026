"""Shared config + paths. Reads .env. No secrets hardcoded (ANTIGRAVITY.md §3)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"

PG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
    "db": os.getenv("PG_DB", "paimana"),
    "user": os.getenv("PG_USER", "paimana"),
    "password": os.getenv("PG_PASSWORD", ""),
}

SEED = 42  # record in every model run for determinism (ANTIGRAVITY.md §5)
