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
    """
    Configuration manager for the hexapod system.
    
    Manages configuration values from multiple sources including environment variables,
    .env files, and command line arguments. Provides validation and access to
    configuration values with proper error handling.
    
    Attributes:
        _config (Dict[str, Any]): Internal dictionary storing configuration values
    """

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
        """
        Get a configuration value.
        
        Args:
            key (str): The configuration key to retrieve
            default (Any, optional): Default value to return if key is not found.
                                   Defaults to None.
        
        Returns:
            Any: The configuration value for the given key, or default if not found
        """
        return self._config.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key (str): The configuration key to set
            value (Any): The value to set for the given key
        """
        self._config[key] = value

    def update_from_args(self, args: argparse.Namespace) -> None:
        """
        Update configuration from command line arguments.
        
        Args:
            args (argparse.Namespace): Parsed command line arguments containing
                                     configuration values to update
        """
        if hasattr(args, "access_key") and args.access_key:
            self._config["picovoice_access_key"] = args.access_key

    def validate(self) -> None:
        """
        Validate required configuration values.
        
        Raises:
            ValueError: If required configuration values are missing or invalid
        """
        if not self._config["picovoice_access_key"]:
            raise ValueError(
                "PICOVOICE_ACCESS_KEY is required. "
                "Set it via environment variable, .env file, or --access-key argument. "
                "Get your free access key from: https://console.picovoice.ai/"
            )

    def get_picovoice_key(self) -> str:
        """
        Get the Picovoice access key.
        
        Returns:
            str: The Picovoice access key for authentication
            
        Raises:
            ValueError: If the Picovoice access key is not set
        """
        key = self._config["picovoice_access_key"]
        if not key:
            raise ValueError("PICOVOICE_ACCESS_KEY is not set")
        return key


def create_config_parser() -> argparse.ArgumentParser:
    """
    Create command line argument parser for Picovoice configuration.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser with Picovoice-specific
                               command line options
    """
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
