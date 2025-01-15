"""
Logger module for the Hexapod project. Provides custom logging levels and formatters.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import datetime as dt
import json

if TYPE_CHECKING:
    from typing import Optional, Dict, Any

# Define built-in log record attributes for custom formatting
LOG_RECORD_BUILTIN_ATTRS = {...}

def add_user_info_level() -> None:
    """
    Initialize and add a custom logging level 'USER_INFO' to the logging module.
    
    This function sets up a new logging level with a numeric value of 25 and 
    associates it with the name "USER_INFO". It also adds the `user_info` method 
    to the `logging.Logger` class for ease of logging at this level.
    """
    USER_INFO_LEVEL = 25
    logging.addLevelName(USER_INFO_LEVEL, "USER_INFO")
    logging.USER_INFO = USER_INFO_LEVEL

    def user_info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a user-level informational message.

        Args:
            message (str): The message to be logged.
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.
        
        Returns:
            None
        """
        if self.isEnabledFor(USER_INFO_LEVEL):
            self._log(USER_INFO_LEVEL, message, args, **kwargs, stacklevel=2)

    logging.Logger.user_info = user_info

add_user_info_level()


class MyJSONFormatter(logging.Formatter):
    """Formatter that outputs logs in JSON format."""

    def __init__(
        self,
        *,
        fmt_keys: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize the JSON formatter with optional format keys.

        Args:
            fmt_keys (Optional[Dict[str, str]]): A dictionary mapping of format keys.
        
        Returns:
            None
        """
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string.

        Args:
            record (logging.LogRecord): The log record to format.
        
        Returns:
            str: The formatted log record as a JSON string.
        """
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)
    
    def _prepare_log_dict(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        Prepare the log record dictionary with specified format keys.

        Args:
            record (logging.LogRecord): The log record to prepare.
        
        Returns:
            Dict[str, Any]: The prepared log record dictionary.
        """
        always_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(record.created, tz=dt.timezone.utc).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: msg_val
            if (msg_val := always_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        return message
    
class VerboseFormatter(logging.Formatter):
    """Formatter that outputs verbose logs with additional context."""

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None, style: str = '%', validate: bool = True) -> None:
        """Initialize the verbose formatter with optional format and date format.

        Args:
            fmt (Optional[str]): The format string for the log messages.
            datefmt (Optional[str]): The date format string.
            style (str): The style of the format string.
            validate (bool): Whether to validate the format string.
        
        Returns:
            None
        """
        if fmt is None:
            fmt = "[%(levelname)s - %(module)s - %(threadName)s - %(funcName)s - Line: %(lineno)-4d] - %(asctime)s - %(message)s"
        if datefmt is None:
            datefmt = "%Y-%m-%dT%H:%M:%S%z"
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, validate=validate)
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with custom spacing.

        Args:
            record (logging.LogRecord): The log record to format.
        
        Returns:
            str: The formatted log record string.
        """
        record.levelname = f"{record.levelname:^9}"
        record.module = f"{record.module:^30}"
        record.threadName = f"{record.threadName:^30}"
        record.funcName = f"{record.funcName:^30}"
        return super().format(record)

class ColoredTerminalFormatter(logging.Formatter):
    """Formatter that adds ANSI color codes to log messages based on severity."""

    # ANSI color codes for different log levels
    ANSI_COLORS = {
        'BLUE': '\033[94m',
        'GREEN': '\033[92m',
        'CYAN': '\033[96m',
        'YELLOW': '\033[93m',
        'RED': '\033[91m',
        'BOLD_RED': '\033[1;31m',
        'MAGENTA': '\033[95m',
        'ORANGE': '\033[38;5;208m',
        'PINK': '\033[38;5;205m',
    }

    # Reset color code to default
    RESET_COLOR = '\033[0m'

    # Log message format string
    FMT = "[{levelname:^9} - {module:^30} - {asctime}] - {message}"

    # Mapping of log levels to their respective formatted strings with colors
    FORMATS = {
        logging.DEBUG: FMT,
        logging.INFO: f"{ANSI_COLORS['GREEN']}{FMT}{RESET_COLOR}",
        logging.USER_INFO: f"{ANSI_COLORS['CYAN']}{FMT}{RESET_COLOR}",
        logging.WARNING: f"{ANSI_COLORS['YELLOW']}{FMT}{RESET_COLOR}",
        logging.ERROR: f"{ANSI_COLORS['RED']}{FMT}{RESET_COLOR}",
        logging.CRITICAL: f"{ANSI_COLORS['BOLD_RED']}{FMT}{RESET_COLOR}",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with color codes.

        Args:
            record (logging.LogRecord): The log record to format.
        
        Returns:
            str: The formatted log record string with ANSI color codes.
        """
        log_fmt = self.FORMATS.get(record.levelno, self.FMT)
        formatter = logging.Formatter(log_fmt, style="{")
        return formatter.format(record)