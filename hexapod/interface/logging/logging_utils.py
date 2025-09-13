"""
Logging utilities for the Hexapod project.

This module provides utility functions for log management including log cleaning,
configuration overrides, and logging setup helpers.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import atexit
import logging
import logging.config
from pathlib import Path

import yaml

if TYPE_CHECKING:
    from typing import Optional

from hexapod.utils import rename_thread

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

def override_log_levels(config: dict, log_level: str) -> dict:
    """
    Override all logger levels in the configuration with the specified log level.
    
    Args:
        config: The logging configuration dictionary
        log_level: Logging level to override all loggers (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        dict: Modified configuration with overridden log levels
    """
    if not log_level:
        return config
    
    # Override root logger level
    if "loggers" in config and "root" in config["loggers"]:
        config["loggers"]["root"]["level"] = log_level
    
    # Override all specific logger levels
    if "loggers" in config:
        for logger_name, logger_config in config["loggers"].items():
            if logger_name != "root":  # Skip root logger as it's handled above
                logger_config["level"] = log_level
    
    # Override handler levels (except stdout which should stay at USER_INFO)
    if "handlers" in config:
        for handler_name, handler_config in config["handlers"].items():
            if handler_name not in ["stdout", "stderr"]:  # Keep stdout/stderr at their original levels
                handler_config["level"] = log_level
    
    return config

def setup_logging(log_dir: Optional[Path] = None, config_file: Optional[Path] = None, log_level: str = 'DEBUG') -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        log_dir: Directory to store log files
        config_file: Path to the logging configuration file
        log_level: Logging level to override all loggers (DEBUG, INFO, WARNING, ERROR)
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
        
        # Override log levels if specified
        config = override_log_levels(config, log_level)
        
        logging.config.dictConfig(config)
        queue_handler = logging.getLogger("root").handlers[0]  # Assuming queue_handler is the first handler
        if queue_handler is not None and hasattr(queue_handler, 'listener'):
            queue_handler.listener.start()
            rename_thread(queue_handler.listener._thread, "QueueHandlerListener")
            atexit.register(queue_handler.listener.stop)
    else:
        raise FileNotFoundError(f"Logging configuration file not found at {config_file}. Custom logging configuration is required.") 