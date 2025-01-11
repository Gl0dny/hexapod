import datetime as dt
import json
import logging
from typing import override

USER_INFO_LEVEL = 25
logging.addLevelName(USER_INFO_LEVEL, "USER_INFO")

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
    
class CenteredStringFormatter(logging.Formatter):
    def format(self, record):
        record.levelname = f"{record.levelname:^9}"
        record.module = f"{record.module:^30}"
        record.threadName = f"{record.threadName:^30}"
        record.funcName = f"{record.funcName:^30}"
        return super().format(record)