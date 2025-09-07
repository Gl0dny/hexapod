"""
Configuration management for the Hexapod Voice Control System.
Handles environment variables, configuration files, and command line arguments.
"""

import os
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv


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
            "audio_device_index": int(os.getenv("AUDIO_DEVICE_INDEX", "-1")),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "log_dir": Path(os.getenv("LOG_DIR", "logs")),
            "enable_manual_control": os.getenv("ENABLE_MANUAL_CONTROL", "true").lower() == "true",
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
    
    def update_from_args(self, args: argparse.Namespace) -> None:
        """Update configuration from command line arguments."""
        if hasattr(args, 'access_key') and args.access_key:
            self._config["picovoice_access_key"] = args.access_key
        if hasattr(args, 'audio_device_index') and args.audio_device_index is not None:
            self._config["audio_device_index"] = args.audio_device_index
        if hasattr(args, 'log_level') and args.log_level:
            self._config["log_level"] = args.log_level
        if hasattr(args, 'log_dir') and args.log_dir:
            self._config["log_dir"] = args.log_dir
    
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
    
    def get_audio_device_index(self) -> int:
        """Get the audio device index."""
        return self._config["audio_device_index"]
    
    def get_log_level(self) -> str:
        """Get the logging level."""
        return self._config["log_level"]
    
    def get_log_dir(self) -> Path:
        """Get the log directory."""
        return self._config["log_dir"]
    
    def is_manual_control_enabled(self) -> bool:
        """Check if manual control is enabled."""
        return self._config["enable_manual_control"]


def create_config_parser() -> argparse.ArgumentParser:
    """Create command line argument parser with configuration options."""
    parser = argparse.ArgumentParser(
        description='Hexapod Voice Control System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration can be provided via:
1. Command line arguments (highest priority)
2. Environment variables
3. .env file in current directory
4. Default values (lowest priority)

Example usage:
  hexapod --access-key "YOUR_PICOVOICE_KEY"
  hexapod --config .env
  PICOVOICE_ACCESS_KEY="your_key" hexapod
        """
    )
    
    # Configuration file
    parser.add_argument('--config', type=Path, default=None,
                        help='Path to .env configuration file')
    
    # Required arguments
    parser.add_argument('--access-key', type=str, default=None,
                        help='Picovoice Access Key for authentication (can also be set via PICOVOICE_ACCESS_KEY env var)')
    
    # Optional arguments
    parser.add_argument('--audio-device-index', type=int, default=None,
                        help='Index of the audio input device (default: autoselect)')
    parser.add_argument('--log-dir', type=Path, default=None,
                        help='Directory to store logs')
    parser.add_argument('--log-config-file', type=Path, 
                        default=Path('src/interface/logging/config/config.yaml'),
                        help='Path to log configuration file')
    parser.add_argument('--log-level', type=str, default=None, 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    parser.add_argument('--clean', '-c', action='store_true',
                        help='Clean all logs in the logs directory.')
    parser.add_argument('--print-context', action='store_true',
                        help='Print context information.')
    parser.add_argument('--disable-manual-control', action='store_true',
                        help='Disable manual gamepad control (voice control only)')
    
    return parser
