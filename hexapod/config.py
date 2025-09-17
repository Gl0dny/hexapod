"""
Configuration management for the Hexapod Voice Control System.
Handles environment variables, configuration files, and command line arguments.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import os
import argparse
from pathlib import Path

from dotenv import load_dotenv

if TYPE_CHECKING:
    from typing import Optional, Dict, Any


class Config:
    """Configuration manager for the hexapod system."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_file: Optional path to .env configuration file
        """
        # Load environment variables from .env file if it exists
        if config_file and config_file.exists():
            load_dotenv(config_file)
        else:
            # Try to load from default locations
            default_config = Path.cwd() / ".env"
            if default_config.exists():
                load_dotenv(default_config)

        # Set default values
        self._config = {
            "picovoice_access_key": os.getenv("PICOVOICE_ACCESS_KEY"),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

    def update_from_args(self, args: argparse.Namespace) -> None:
        """Update configuration from command line arguments."""
        if hasattr(args, "access_key") and args.access_key:
            self._config["picovoice_access_key"] = args.access_key

    def validate(self) -> None:
        """Validate required configuration values."""
        if not self._config["picovoice_access_key"]:
            raise ValueError(
                "PICOVOICE_ACCESS_KEY is required. "
                "Set it via environment variable, .env file, or --access-key argument. "
                "Get your free access key from: https://console.picovoice.ai/"
            )

    def get_picovoice_key(self) -> str:
        """Get the Picovoice access key."""
        key = self._config["picovoice_access_key"]
        if not key:
            raise ValueError("PICOVOICE_ACCESS_KEY is not set")
        return key


def create_config_parser() -> argparse.ArgumentParser:
    """Create command line argument parser for Picovoice configuration."""
    parser = argparse.ArgumentParser(
        description="Hexapod Voice Control System - Picovoice Configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Picovoice configuration can be provided via:
1. Command line arguments (highest priority)
2. Environment variables
3. .env file in current directory
        """,
    )

    # Required arguments
    parser.add_argument(
        "--access-key",
        type=str,
        default=None,
        help="Picovoice Access Key for authentication (can also be set via PICOVOICE_ACCESS_KEY env var)",
    )

    return parser
