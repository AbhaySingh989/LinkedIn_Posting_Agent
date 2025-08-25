
import logging
import sys
from src.json_log_formatter import JsonFormatter

def setup_logging(log_level="INFO"):
    """
    Sets up logging for the application.

    Args:
        log_level (str): The minimum log level to capture (e.g., "DEBUG", "INFO").
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a handler to print to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)

    # Create a formatter and set it for the handler
    formatter = JsonFormatter()
    stream_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(stream_handler)

    logging.info(f"Logging setup complete with level {log_level}")

