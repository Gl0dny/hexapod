from __future__ import annotations
from typing import TYPE_CHECKING
import atexit
import logging
import logging.config
from pathlib import Path

import yaml

if TYPE_CHECKING:
    from typing import Optional

from utils import rename_thread

def clean_logs(log_dir: Optional[Path] = None) -> None:
    """
    Clean all log files in the specified directory.
    
    Args:
        log_dir: Directory containing log files to clean. If None, uses the project root.
    """
    if log_dir is None:
        log_dir = Path(__file__).resolve().parent.parent.parent.parent
    
    log_patterns = ['*.log', '*.log.*', '*.log.jsonl', '*.log.json']
    for pattern in log_patterns:
        for log_file in log_dir.rglob(pattern):
            log_file.unlink()

def setup_logging(log_dir: Optional[Path] = None, config_file: Optional[Path] = None) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        log_dir: Directory to store log files
        config_file: Path to the logging configuration file
    """
    if config_file is None:
        log_dir = Path("logs")
    
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    if config_file is None:
        config_file = Path(__file__).parent / "config" / "config.yaml"

    if config_file.is_file():
        with open(config_file, "rt") as f:
            config = yaml.safe_load(f)
        
        # Update handler filenames to use the provided log_dir
        for handler_name, handler in config.get("handlers", {}).items():
            filename = handler.get("filename")
            if filename:
                handler["filename"] = str(log_dir / Path(filename).name)  # Set to log_dir/<basename>
        
        logging.config.dictConfig(config)
        queue_handler = logging.getLogger("root").handlers[0]  # Assuming queue_handler is the first handler
        if queue_handler is not None and hasattr(queue_handler, 'listener'):
            queue_handler.listener.start()
            rename_thread(queue_handler.listener._thread, "QueueHandlerListener")
            atexit.register(queue_handler.listener.stop)
    else:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("main_logger")
        logger.warning(f"Logging configuration file not found at {config_file}. Using basic logging configuration") 