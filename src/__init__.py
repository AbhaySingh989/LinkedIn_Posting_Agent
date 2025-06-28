# This file makes the 'src' directory a Python package.

# Optionally, you can make specific modules or functions available
# when the package is imported. For example:
#
# from src.article_fetcher import ArticleFetcher # Example
# from .llm_handler import LLMHandler # Example
# from .telegram_bot import TelegramNotifier # Example
# from .linkedin_poster import LinkedInPoster # Example
# from .utils import setup_logging, Article # Example
# from .json_log_formatter import JSONLogFormatter # Example

# This allows imports like:
# from src import ArticleFetcher # (If uncommented above)

# For now, we'll keep it simple.
# The individual modules will be imported directly where needed, e.g.,
# from src.article_fetcher import ArticleFetcher
import logging

# Configure a basic logger for the package if no other logging is configured.
# This is helpful for library-like usage, but applications (like main.py)
# should ideally configure their own logging.
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logger.addHandler(logging.NullHandler())

# Define common data structures if any, e.g., Article dataclass
# (though it's currently in utils.py, it could be here too)
