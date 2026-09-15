"""Stage: models — see docs/steps/ for the spec that governs this stage.

Entry point: run(config). Reads interim/processed, never mutates data/raw.
Do not implement until the corresponding STEP file is marked IN PROGRESS in PROGRESS.md.
"""

from src.common.logging_setup import get_logger

log = get_logger("models")


def run(config: dict | None = None):
    raise NotImplementedError(
        "models not implemented. Follow docs/steps/ for 'models' before coding, "
        "and update docs per docs/09_DOC_SYNC_RULES.md when done."
    )


if __name__ == "__main__":
    run()
