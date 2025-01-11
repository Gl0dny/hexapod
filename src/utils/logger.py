import datetime as dt
import json
import logging
from typing import override

USER_INFO_LEVEL = 25
logging.addLevelName(USER_INFO_LEVEL, "USER_INFO")
logging.USER_INFO = USER_INFO_LEVEL

def user_info(self, message, *args, **kwargs):
    if self.isEnabledFor(USER_INFO_LEVEL):
        self._log(USER_INFO_LEVEL, message, args, **kwargs, stacklevel=2)

logging.Logger.user_info = user_info


LOG_RECORD_BUILTIN_ATTRS = {...}

class MyJSONFormatter(logging.Formatter):
    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
    ):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)
    
    def _prepare_log_dict(self, record: logging.LogRecord):
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
    def __init__(self, fmt=None, datefmt=None, style='%', validate=True):
        if fmt is None:
            fmt = "[%(levelname)s - %(module)s - %(threadName)s - %(funcName)s - Line: %(lineno)-4d] - %(asctime)s - %(message)s"
        if datefmt is None:
            datefmt = "%Y-%m-%dT%H:%M:%S%z"
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, validate=validate)
    
    def format(self, record):
        record.levelname = f"{record.levelname:^9}"
        record.module = f"{record.module:^30}"
        record.threadName = f"{record.threadName:^30}"
        record.funcName = f"{record.funcName:^30}"
        return super().format(record)
    
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

RESET_COLOR = '\033[0m'

FMT = "[{levelname:^9} - {module:^30} - {asctime}] - {message}"

FORMATS = {
    logging.DEBUG: FMT,
    logging.INFO: f"{ANSI_COLORS['GREEN']}{FMT}{RESET_COLOR}",
    logging.USER_INFO: f"{ANSI_COLORS['CYAN']}{FMT}{RESET_COLOR}",
    logging.WARNING: f"{ANSI_COLORS['YELLOW']}{FMT}{RESET_COLOR}",
    logging.ERROR: f"{ANSI_COLORS['RED']}{FMT}{RESET_COLOR}",
    logging.CRITICAL: f"{ANSI_COLORS['BOLD_RED']}{FMT}{RESET_COLOR}",
}

class ColoredTerminalFormatter(logging.Formatter):
    def format(self, record):
        log_fmt = FORMATS[record.levelno]
        log_fmt = FORMATS[record.levelno]
        formatter = logging.Formatter(log_fmt, style="{")
        return formatter.format(record)