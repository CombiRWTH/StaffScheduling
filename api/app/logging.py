import logging
import sys


def configure_logging(*, level: str = "INFO") -> None:
    """Configure application logging once at process startup."""
    normalized_level = level.strip().upper()
    numeric_level = logging.getLevelNamesMapping().get(normalized_level)

    if numeric_level is None:
        raise ValueError(f"Invalid log level: {level!r}")

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
        root_logger.addHandler(handler)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
