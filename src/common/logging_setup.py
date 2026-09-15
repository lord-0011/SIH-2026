"""Central logging. Validation/matching stages log every flag with a reason."""

import logging


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )
    return logging.getLogger(name)
