import logging
import sys

def setup_logger(name: str = "onboarding", level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a consistent logger for the entire project.

    - Configures the root logger once (first import).
    - Subsequent calls reuse the same configuration.
    - Prevents duplicate handlers.
    - Each module can call this safely: logger = setup_logger(__name__)

    Args:
        name: The name for the logger (usually __name__).
        level: Logging level (default: INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Configure the root logger only once
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(level)

    # Ensure all child loggers propagate to the root
    logger.propagate = True
    return logger

