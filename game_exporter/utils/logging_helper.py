import json
import logging
import sys


class CustomFormatter(logging.Formatter):
    def format(self, record) -> str:
        """Format the log record with padding for the log level, prepend emojis, and add color coding.

        If the log message is a JSON string or a dictionary, pretty-print it.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message.
        """
        # Define emojis for each log level
        level_emojis = {
            "DEBUG": "🐛",
            "INFO": "ℹ️ ",
            "WARNING": "⚠️ ",
            "ERROR": "❌",
            "CRITICAL": "🚨",
        }

        # Define color codes for each log level
        level_colors = {
            "DEBUG": "\033[94m",  # Blue
            "INFO": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",  # Red
            "CRITICAL": "\033[95m",  # Magenta
        }

        # Reset color code
        reset_color = "\033[0m"

        # Get the emoji and color for the current log level
        emoji = level_emojis.get(record.levelname, "")
        color = level_colors.get(record.levelname, "")

        # Check if the message is JSON or a dictionary and pretty-print it
        try:
            if isinstance(record.msg, dict):
                record.msg = json.dumps(record.msg, indent=4, sort_keys=True)
            else:
                # Attempt to parse the message as JSON
                record.msg = json.dumps(
                    json.loads(record.msg), indent=4, sort_keys=True
                )
        except (json.JSONDecodeError, TypeError):
            # If it's not JSON or a dictionary, leave the message as is
            pass

        # ensure JSON messages start on a new line for better readability
        if record.msg.startswith("{"):
            record.msg = "\n" + record.msg
        # Define the log format with padding for log level and prepend the emoji
        log_format = f"%(asctime)s {emoji}{color} %(levelname)-8s {reset_color}%(funcName)-15s --> {color}%(message)s{reset_color}"
        formatter = logging.Formatter(log_format)
        return formatter.format(record)


def setup_logger(name: str, level: str) -> logging.Logger:
    """Setup a logger with a stream handler and a specific log level.

    The logging level can be set using the environment variable.

    Can be one of the following values:
    - DEBUG
    - INFO (default)
    - WARNING
    - ERROR
    - CRITICAL

    Args:
        name (str): The name of the logger.
        level (str): The logging level as a string.

    Returns:
        logging.Logger: The logger instance.
    """

    # Create a stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(CustomFormatter())

    # Get the logger instance
    logger = logging.getLogger(name)

    # It's important to check if the logger already has handlers to avoid logging messages multiple times
    # when you create a new instance of your logger in different modules.
    if logger.hasHandlers():
        logger.handlers.clear()

    # Define a mapping from string to logging levels
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # Get the logging level from an environment variable (default to INFO if not set or invalid)

    log_level = log_levels.get(level.upper(), logging.INFO)

    # Set the logging level
    stream_handler.setLevel(log_level)
    logger.setLevel(log_level)

    logger.addHandler(stream_handler)

    return logger
