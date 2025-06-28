import logging
import json
from datetime import datetime

class JSONLogFormatter(logging.Formatter):
    """
    Custom log formatter to output log records as JSON objects.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(), # Get the formatted log message
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }

        # Include exception information if present
        if record.exc_info:
            # formatException will give the full traceback string
            log_object["exception"] = self.formatException(record.exc_info)

        # Include stack information if present (e.g. from logger.exception or stack_info=True)
        if record.stack_info:
            log_object["stack_info"] = self.formatStack(record.stack_info)

        # Add any extra fields passed to the logger
        # These are fields that are not part of the standard LogRecord attributes
        standard_attrs = set(logging.LogRecord("", 0, "", 0, "", (), None, None).__dict__.keys())
        extra_attrs = {}
        for key, value in record.__dict__.items():
            if key not in standard_attrs and key not in ['message', 'asctime', 'args']: # 'message', 'asctime', 'args' are handled or not needed raw
                extra_attrs[key] = value
        if extra_attrs:
            log_object["extra"] = extra_attrs

        return json.dumps(log_object)

if __name__ == '__main__':
    # Example usage of the JSONLogFormatter
    logger = logging.getLogger('json_test_logger')
    logger.setLevel(logging.DEBUG)

    # Console handler with standard formatter for comparison
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Console handler with JSON formatter
    json_console_handler = logging.StreamHandler()
    json_console_handler.setFormatter(JSONLogFormatter())
    logger.addHandler(json_console_handler)

    # Test log messages
    logger.debug("This is a debug message with some extra info.", extra={"key1": "value1", "user_id": 123})
    logger.info("Standard info message.")
    logger.warning("A warning occurred.")
    logger.error("An error happened here.")

    try:
        x = 1 / 0
    except ZeroDivisionError:
        logger.exception("ZeroDivisionError occurred (logged with logger.exception).") # Automatically includes exc_info

    logger.critical("Critical error!", stack_info=True, extra={"status_code": 500})

    # Example of how it might look in a file (by redirecting one handler to a file)
    # import os
    # if not os.path.exists("logs"):
    #     os.makedirs("logs")
    # json_file_handler = logging.FileHandler("logs/test_app.log.json", mode='w')
    # json_file_handler.setFormatter(JSONLogFormatter())
    # logger.removeHandler(json_console_handler) # Remove one console handler if adding file
    # logger.addHandler(json_file_handler)
    # logger.info("This message will go to the JSON file and standard console.")
    # print("\nCheck 'logs/test_app.log.json' for JSON formatted output (if file handler was enabled).")
