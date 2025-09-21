"""
Unit tests for configuration management.
"""

import pytest
import os
import argparse
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from hexapod.config import Config, create_config_parser


class TestConfig:
    """Test cases for Config class."""

    def test_init_without_config_file(self):
        """Test Config initialization without config file."""
        with (
            patch("hexapod.config.load_dotenv") as mock_load_dotenv,
            patch("hexapod.config.Path.cwd") as mock_cwd,
            patch("hexapod.config.Path.exists") as mock_exists,
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            mock_cwd.return_value = Path("/test")
            mock_exists.return_value = False

            config = Config()

            # Should not call load_dotenv since no config file provided
            mock_load_dotenv.assert_not_called()
            assert config.get("picovoice_access_key") == "test_key"

    def test_init_with_nonexistent_config_file(self):
        """Test Config initialization with non-existent config file."""
        with (
            patch("hexapod.config.load_dotenv") as mock_load_dotenv,
            patch("hexapod.config.Path.cwd") as mock_cwd,
            patch("hexapod.config.Path.exists") as mock_exists,
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            mock_cwd.return_value = Path("/test")
            mock_exists.return_value = False
            config_file = Path("/nonexistent/.env")

            config = Config(config_file)

            # Should not call load_dotenv since file doesn't exist
            mock_load_dotenv.assert_not_called()
            assert config.get("picovoice_access_key") == "test_key"

    def test_init_with_existing_config_file(self):
        """Test Config initialization with existing config file."""
        with (
            patch("hexapod.config.load_dotenv") as mock_load_dotenv,
            patch("hexapod.config.Path.exists") as mock_exists,
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            mock_exists.return_value = True
            config_file = Path("/existing/.env")

            config = Config(config_file)

            # Should call load_dotenv with the provided file
            mock_load_dotenv.assert_called_once_with(config_file)
            assert config.get("picovoice_access_key") == "test_key"

    def test_init_with_default_config_file(self):
        """Test Config initialization with default config file found."""
        with (
            patch("hexapod.config.load_dotenv") as mock_load_dotenv,
            patch("hexapod.config.Path.cwd") as mock_cwd,
            patch("hexapod.config.Path.exists") as mock_exists,
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            mock_cwd.return_value = Path("/test")
            mock_exists.return_value = True
            default_config = Path("/test/.env")

            config = Config()

            # Should call load_dotenv with default config file
            mock_load_dotenv.assert_called_once_with(default_config)
            assert config.get("picovoice_access_key") == "test_key"

    def test_init_without_env_variable(self):
        """Test Config initialization without environment variable."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {}, clear=True),
        ):

            config = Config()
            assert config.get("picovoice_access_key") is None

    def test_get_existing_key(self):
        """Test getting an existing configuration key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            assert config.get("picovoice_access_key") == "test_key"

    def test_get_nonexistent_key_with_default(self):
        """Test getting a non-existent key with default value."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            assert config.get("nonexistent_key", "default_value") == "default_value"

    def test_get_nonexistent_key_without_default(self):
        """Test getting a non-existent key without default value."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            assert config.get("nonexistent_key") is None

    def test_set_value(self):
        """Test setting a configuration value."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            config.set_value("new_key", "new_value")
            assert config.get("new_key") == "new_value"

    def test_set_value_overwrite(self):
        """Test overwriting an existing configuration value."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            config.set_value("picovoice_access_key", "new_key")
            assert config.get("picovoice_access_key") == "new_key"

    def test_update_from_args_with_access_key(self):
        """Test updating configuration from args with access key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            args = argparse.Namespace(access_key="new_access_key")
            config.update_from_args(args)
            assert config.get("picovoice_access_key") == "new_access_key"

    def test_update_from_args_without_access_key(self):
        """Test updating configuration from args without access key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            args = argparse.Namespace()
            config.update_from_args(args)
            assert config.get("picovoice_access_key") == "test_key"

    def test_update_from_args_with_none_access_key(self):
        """Test updating configuration from args with None access key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            args = argparse.Namespace(access_key=None)
            config.update_from_args(args)
            assert config.get("picovoice_access_key") == "test_key"

    def test_update_from_args_with_empty_access_key(self):
        """Test updating configuration from args with empty access key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            args = argparse.Namespace(access_key="")
            config.update_from_args(args)
            # Empty string is falsy, so config should not be updated
            assert config.get("picovoice_access_key") == "test_key"

    def test_validate_with_valid_key(self):
        """Test validation with valid access key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            # Should not raise any exception
            config.validate()

    def test_validate_with_none_key(self):
        """Test validation with None access key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {}, clear=True),
        ):

            config = Config()
            with pytest.raises(ValueError, match="PICOVOICE_ACCESS_KEY is required"):
                config.validate()

    def test_validate_with_empty_key(self):
        """Test validation with empty access key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": ""}),
        ):

            config = Config()
            with pytest.raises(ValueError, match="PICOVOICE_ACCESS_KEY is required"):
                config.validate()

    def test_get_picovoice_key_with_valid_key(self):
        """Test getting Picovoice key with valid key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            assert config.get_picovoice_key() == "test_key"

    def test_get_picovoice_key_with_none_key(self):
        """Test getting Picovoice key with None key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {}, clear=True),
        ):

            config = Config()
            with pytest.raises(ValueError, match="PICOVOICE_ACCESS_KEY is not set"):
                config.get_picovoice_key()

    def test_get_picovoice_key_with_empty_key(self):
        """Test getting Picovoice key with empty key."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": ""}),
        ):

            config = Config()
            with pytest.raises(ValueError, match="PICOVOICE_ACCESS_KEY is not set"):
                config.get_picovoice_key()

    def test_config_dict_initialization(self):
        """Test that config dictionary is properly initialized."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(os.environ, {"PICOVOICE_ACCESS_KEY": "test_key"}),
        ):

            config = Config()
            assert isinstance(config._config, dict)
            assert "picovoice_access_key" in config._config
            assert config._config["picovoice_access_key"] == "test_key"

    def test_config_with_multiple_env_vars(self):
        """Test config with multiple environment variables."""
        with (
            patch("hexapod.config.load_dotenv"),
            patch("hexapod.config.Path.cwd"),
            patch("hexapod.config.Path.exists", return_value=False),
            patch.dict(
                os.environ,
                {"PICOVOICE_ACCESS_KEY": "test_key", "OTHER_VAR": "other_value"},
            ),
        ):

            config = Config()
            assert config.get("picovoice_access_key") == "test_key"
            assert config.get("OTHER_VAR") is None  # Only picovoice_key is loaded


class TestCreateConfigParser:
    """Test cases for create_config_parser function."""

    def test_create_config_parser(self):
        """Test creating argument parser."""
        parser = create_config_parser()

        assert isinstance(parser, argparse.ArgumentParser)
        assert (
            parser.description
            == "Hexapod Voice Control System - Picovoice Configuration"
        )
        assert parser.formatter_class == argparse.RawDescriptionHelpFormatter

    def test_parser_has_access_key_argument(self):
        """Test that parser has access-key argument."""
        parser = create_config_parser()

        # Parse known args to test argument exists
        args = parser.parse_args(["--access-key", "test_key"])
        assert args.access_key == "test_key"

    def test_parser_access_key_default(self):
        """Test that access-key argument has correct default."""
        parser = create_config_parser()

        # Parse with no arguments
        args = parser.parse_args([])
        assert args.access_key is None

    def test_parser_help_text(self):
        """Test that parser has correct help text."""
        parser = create_config_parser()

        # Get help text
        help_text = parser.format_help()
        assert "Hexapod Voice Control System" in help_text
        assert "Picovoice Configuration" in help_text
        assert "access-key" in help_text
        assert "PICOVOICE_ACCESS_KEY" in help_text

    def test_parser_epilog(self):
        """Test that parser has correct epilog."""
        parser = create_config_parser()

        # Get help text
        help_text = parser.format_help()
        assert "Command line arguments" in help_text
        assert "Environment variables" in help_text
        assert ".env file" in help_text

    def test_parser_with_help_flag(self):
        """Test parser with --help flag."""
        parser = create_config_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

    def test_parser_with_unknown_argument(self):
        """Test parser with unknown argument."""
        parser = create_config_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["--unknown-arg", "value"])

    def test_parser_access_key_type(self):
        """Test that access-key argument accepts string type."""
        parser = create_config_parser()

        # Test with string value
        args = parser.parse_args(["--access-key", "string_key"])
        assert isinstance(args.access_key, str)
        assert args.access_key == "string_key"

    def test_parser_access_key_with_spaces(self):
        """Test access-key argument with spaces."""
        parser = create_config_parser()

        args = parser.parse_args(["--access-key", "key with spaces"])
        assert args.access_key == "key with spaces"

    def test_parser_access_key_empty_string(self):
        """Test access-key argument with empty string."""
        parser = create_config_parser()

        args = parser.parse_args(["--access-key", ""])
        assert args.access_key == ""
