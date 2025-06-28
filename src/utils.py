import logging
import logging.config
import sys
from dataclasses import dataclass, field
from typing import Optional, List

# Re-define Article dataclass here if it's not imported from article_fetcher
# to avoid circular dependencies if other utils need Article but article_fetcher needs utils.
# For now, assuming Article is primarily defined and used by article_fetcher and passed around.
# If Article becomes a more central data structure used by utils, define it here.
# from .article_fetcher import Article # This would create circular dependency if article_fetcher imports utils

@dataclass
class Article: # Duplicating definition here to make it available for other modules if they import utils
    title: str
    url: str
    source: str
    summary: Optional[str] = None
    # content: Optional[str] = None # Full content, if fetched and needed for other utils

def setup_logging(log_level: str = "INFO", config=None):
    """
    Sets up basic logging for the application.
    Allows configuration via a passed config object or defaults.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Basic configuration for console logging
    # More advanced configuration could be loaded from a file or dict
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False, # Keep existing loggers (e.g. from libraries)
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'level': level,
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': sys.stdout, # Default to stdout
            },
            # Example: File handler (can be added if needed)
            # 'file': {
            #     'level': level,
            #     'formatter': 'standard',
            #     'class': 'logging.FileHandler',
            #     'filename': 'app.log', # Configure filename
            #     'mode': 'a',
            # },
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console'], # Add 'file' here if file logging is enabled
                'level': level,
                'propagate': True,
            },
            # Example: Quieter logging for noisy libraries
            'selenium.webdriver.remote.remote_connection': {
                'handlers': ['console'],
                'level': 'WARNING', # Reduce noise from Selenium internal logs
                'propagate': False, # Don't pass to root logger if handled here
            },
            'urllib3.connectionpool': {
                 'handlers': ['console'],
                 'level': 'WARNING',
                 'propagate': False,
            },
            'httpx': { # python-telegram-bot uses httpx
                 'handlers': ['console'],
                 'level': 'WARNING',
                 'propagate': False,
            }
        }
    }

    if config and hasattr(config, 'log_file_path') and config.log_file_path:
        # If a log file path is provided in config, add a file handler
        logging_config['handlers']['file'] = {
            'level': level,
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': config.log_file_path,
            'mode': 'a',
        }
        logging_config['loggers']['']['handlers'].append('file')

    logging.config.dictConfig(logging_config)

    # After configuring, get the root logger and ensure its level is also set
    # (sometimes dictConfig doesn't set root level as expected for all scenarios)
    # logging.getLogger().setLevel(level) # Ensure root logger level is set if issues persist

    # Add JSON file handler if path is provided in config
    if config and hasattr(config, 'log_json_file_path') and config.log_json_file_path:
        from .json_log_formatter import JSONLogFormatter # Keep import here to avoid circular if JSONLogFormatter needs utils

        json_handler = logging.FileHandler(config.log_json_file_path, mode='a')
        json_handler.setLevel(level)
        json_handler.setFormatter(JSONLogFormatter())
        logging_config['handlers']['json_file'] = { # Add definition for completeness, though configured above
            'class': 'logging.FileHandler',
            'formatter': 'json_formatter_config', # Placeholder, actual formatter set on handler instance
            'level': level,
            'filename': config.log_json_file_path,
        }
        # Add to root logger's handlers
        # Check if 'json_file' handler is already attached from a previous call (e.g. in testing)
        # This is a bit hacky; ideally, setup_logging is called once.
        root_logger_config = logging_config['loggers']['']
        if not any(hdlr for hdlr in logging.getLogger().handlers if isinstance(hdlr, logging.FileHandler) and hdlr.baseFilename == json_handler.baseFilename):
             logging.getLogger().addHandler(json_handler)

        # For other configured loggers, if they don't propagate, they won't use the root's json_handler.
        # If JSON logging is desired for them too, their handlers list would need updating.
        # For simplicity, JSON logging primarily targets the root logger here.


    logging.config.dictConfig(logging_config) # Re-apply config if changed, or apply for the first time

    # If text file logging was added dynamically, ensure the root logger picks it up
    # This part can be tricky if dictConfig was already called. It's often better to build the full config dict first.
    # The current structure adds handlers to the root logger instance if they were dynamically created.
    if config and hasattr(config, 'log_file_path') and config.log_file_path:
        # Check if text file handler already exists to avoid duplicates if setup_logging is called multiple times
        if not any(hdlr for hdlr in logging.getLogger().handlers if isinstance(hdlr, logging.FileHandler) and \
                   not isinstance(hdlr.formatter, JSONLogFormatter) and \
                   hdlr.baseFilename == config.log_file_path):

            text_file_handler = logging.FileHandler(config.log_file_path, mode='a')
            text_file_handler.setLevel(level)
            text_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
            logging.getLogger().addHandler(text_file_handler)


    logger = logging.getLogger(__name__)
    logger.info(f"Logging setup complete. Root effective log level: {logging.getLevelName(logging.getLogger().getEffectiveLevel())}.")
    # For specific loggers like selenium, their effective level might be different due to specific rules.
    # logger.info(f"Selenium logger effective level: {logging.getLevelName(logging.getLogger('selenium').getEffectiveLevel())}")
    handlers_info = [type(h).__name__ for h in logging.getLogger().handlers]
    logger.debug(f"Root logger handlers: {handlers_info}")


# Example of another utility function:
def clean_text(text: str) -> str:
    """
    Basic text cleaning: removes extra whitespace and normalizes line breaks.
    """
    if not text:
        return ""
    text = text.replace('\r\n', '\n').replace('\r', '\n') # Normalize line breaks
    text = ' '.join(text.split()) # Remove extra spaces, tabs, and newlines (makes it single line)
    return text.strip()


if __name__ == "__main__":
    # Test logging setup
    # To test with a config object:
    # class MockConfig:
    #     log_level = "DEBUG"
    #     # log_file_path = "test_app.log" # Uncomment to test file logging
    # cfg = MockConfig()
    # setup_logging(log_level=cfg.log_level, config=cfg)

    setup_logging(log_level="DEBUG") # Default test without config object

    logger_main = logging.getLogger() # Root logger
    logger_utils = logging.getLogger(__name__) # Logger for this module
    logger_selenium = logging.getLogger("selenium.webdriver.remote.remote_connection")

    logger_main.debug("This is a root debug message.")
    logger_main.info("This is a root info message.")
    logger_utils.debug("This is a utils module debug message.")
    logger_utils.info("This is a utils module info message.")
    logger_utils.warning("This is a utils module warning.")
    logger_selenium.debug("This is a selenium debug message (should not appear if level is WARNING).")
    logger_selenium.warning("This is a selenium warning message (should appear).")


    # Test clean_text
    print("\n--- Testing clean_text ---")
    test_str1 = "  Hello   World\nThis is a test.\r\nAnother line.  "
    print(f"Original: '{test_str1}'")
    print(f"Cleaned:  '{clean_text(test_str1)}'")

    test_str2 = "\tExtra\t spaces \n and \n newlines\r\n\r\n"
    print(f"Original: '{test_str2}'")
    print(f"Cleaned:  '{clean_text(test_str2)}'")

    test_str3 = ""
    print(f"Original: '{test_str3}'")
    print(f"Cleaned:  '{clean_text(test_str3)}'")

    test_str4 = "SingleLine"
    print(f"Original: '{test_str4}'")
    print(f"Cleaned:  '{clean_text(test_str4)}'")

    # Example Article usage (if defined in this file)
    # article = Article(title="Test", url="http://example.com", source="Test")
    # print(f"\nArticle: {article}")
