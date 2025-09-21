"""
Unit tests for logging utilities.
"""

import pytest
import tempfile
import yaml
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import logging.config

from hexapod.interface.logging.logging_utils import (
    clean_logs,
    override_log_levels,
    setup_logging,
)


class TestCleanLogs:
    """Test cases for clean_logs function."""

    def test_clean_logs_default_directory(self, tmp_path):
        """Test cleaning logs with default directory."""
        # Create some test log files
        log_files = [
            tmp_path / "test.log",
            tmp_path / "test.log.1",
            tmp_path / "test.log.jsonl",
            tmp_path / "test.log.json",
        ]

        for log_file in log_files:
            log_file.write_text("test log content")
            assert log_file.exists()

        # Mock the default directory to use our temp directory
        with patch("hexapod.interface.logging.logging_utils.Path") as mock_path:
            mock_path.return_value.resolve.return_value = tmp_path
            mock_path.return_value.rglob = tmp_path.rglob

            clean_logs()

        # Check that all log files were deleted
        for log_file in log_files:
            assert not log_file.exists()

    def test_clean_logs_custom_directory(self, tmp_path):
        """Test cleaning logs with custom directory."""
        # Create some test log files
        log_files = [
            tmp_path / "app.log",
            tmp_path / "app.log.1",
            tmp_path / "app.log.jsonl",
            tmp_path / "app.log.json",
        ]

        for log_file in log_files:
            log_file.write_text("test log content")
            assert log_file.exists()

        clean_logs(tmp_path)

        # Check that all log files were deleted
        for log_file in log_files:
            assert not log_file.exists()

    def test_clean_logs_nested_directories(self, tmp_path):
        """Test cleaning logs in nested directories."""
        # Create nested directory structure with log files
        nested_dir = tmp_path / "logs" / "subdir"
        nested_dir.mkdir(parents=True)

        log_files = [
            tmp_path / "main.log",
            tmp_path / "logs" / "nested.log",
            nested_dir / "deep.log",
        ]

        for log_file in log_files:
            log_file.write_text("test log content")
            assert log_file.exists()

        clean_logs(tmp_path)

        # Check that all log files were deleted
        for log_file in log_files:
            assert not log_file.exists()

    def test_clean_logs_no_files(self, tmp_path):
        """Test cleaning logs when no log files exist."""
        # Should not raise an exception
        clean_logs(tmp_path)

        # Directory should still exist
        assert tmp_path.exists()

    def test_clean_logs_partial_failure(self, tmp_path):
        """Test cleaning logs when some files can't be deleted."""
        # Create a log file
        log_file = tmp_path / "test.log"
        log_file.write_text("test content")

        # Mock unlink to raise an exception for some files
        with patch.object(Path, "unlink", side_effect=OSError("Permission denied")):
            # Should raise an exception when files can't be deleted
            with pytest.raises(OSError, match="Permission denied"):
                clean_logs(tmp_path)

    def test_clean_logs_different_patterns(self, tmp_path):
        """Test cleaning logs with different file patterns."""
        # Create files with different patterns
        test_files = [
            tmp_path / "app.log",
            tmp_path / "app.log.1",
            tmp_path / "app.log.2",
            tmp_path / "app.log.jsonl",
            tmp_path / "app.log.json",
            tmp_path / "other.txt",  # Should not be deleted
            tmp_path / "config.yaml",  # Should not be deleted
        ]

        for file_path in test_files:
            file_path.write_text("test content")
            assert file_path.exists()

        clean_logs(tmp_path)

        # Check that only log files were deleted
        log_files = [f for f in test_files if f.suffix == ".log" or ".log." in f.name]
        other_files = [f for f in test_files if f not in log_files]

        for log_file in log_files:
            assert not log_file.exists()

        for other_file in other_files:
            assert other_file.exists()


class TestOverrideLogLevels:
    """Test cases for override_log_levels function."""

    def test_override_log_levels_empty_config(self):
        """Test overriding log levels with empty config."""
        config = {}
        result = override_log_levels(config, "INFO")
        assert result == {}

    def test_override_log_levels_none_level(self):
        """Test overriding log levels with None level."""
        config = {
            "loggers": {"root": {"level": "DEBUG"}, "test_logger": {"level": "INFO"}}
        }
        result = override_log_levels(config, None)
        assert result == config  # Should return unchanged

    def test_override_log_levels_empty_level(self):
        """Test overriding log levels with empty level."""
        config = {
            "loggers": {"root": {"level": "DEBUG"}, "test_logger": {"level": "INFO"}}
        }
        result = override_log_levels(config, "")
        assert result == config  # Should return unchanged

    def test_override_log_levels_root_logger(self):
        """Test overriding log levels for root logger."""
        config = {"loggers": {"root": {"level": "DEBUG"}}}
        result = override_log_levels(config, "WARNING")
        assert result["loggers"]["root"]["level"] == "WARNING"

    def test_override_log_levels_specific_loggers(self):
        """Test overriding log levels for specific loggers."""
        config = {
            "loggers": {
                "root": {"level": "DEBUG"},
                "test_logger": {"level": "INFO"},
                "another_logger": {"level": "ERROR"},
            }
        }
        result = override_log_levels(config, "WARNING")

        assert result["loggers"]["root"]["level"] == "WARNING"
        assert result["loggers"]["test_logger"]["level"] == "WARNING"
        assert result["loggers"]["another_logger"]["level"] == "WARNING"

    def test_override_log_levels_handlers(self):
        """Test overriding log levels for handlers."""
        config = {
            "handlers": {
                "file_handler": {"level": "DEBUG"},
                "console_handler": {"level": "INFO"},
                "stdout": {"level": "USER_INFO"},
                "stderr": {"level": "WARNING"},
            }
        }
        result = override_log_levels(config, "ERROR")

        assert result["handlers"]["file_handler"]["level"] == "ERROR"
        assert result["handlers"]["console_handler"]["level"] == "ERROR"
        # stdout and stderr should not be overridden
        assert result["handlers"]["stdout"]["level"] == "USER_INFO"
        assert result["handlers"]["stderr"]["level"] == "WARNING"

    def test_override_log_levels_complete_config(self):
        """Test overriding log levels with complete configuration."""
        config = {
            "loggers": {
                "root": {"level": "DEBUG"},
                "main_logger": {"level": "INFO"},
                "test_logger": {"level": "WARNING"},
            },
            "handlers": {
                "file_handler": {"level": "DEBUG"},
                "console_handler": {"level": "INFO"},
                "stdout": {"level": "USER_INFO"},
                "stderr": {"level": "ERROR"},
            },
        }
        result = override_log_levels(config, "CRITICAL")

        # Check loggers
        assert result["loggers"]["root"]["level"] == "CRITICAL"
        assert result["loggers"]["main_logger"]["level"] == "CRITICAL"
        assert result["loggers"]["test_logger"]["level"] == "CRITICAL"

        # Check handlers (except stdout/stderr)
        assert result["handlers"]["file_handler"]["level"] == "CRITICAL"
        assert result["handlers"]["console_handler"]["level"] == "CRITICAL"
        # stdout and stderr should not be overridden
        assert result["handlers"]["stdout"]["level"] == "USER_INFO"
        assert result["handlers"]["stderr"]["level"] == "ERROR"

    def test_override_log_levels_no_loggers_section(self):
        """Test overriding log levels when no loggers section exists."""
        config = {"handlers": {"file_handler": {"level": "DEBUG"}}}
        result = override_log_levels(config, "INFO")

        # Should not raise an exception
        assert result["handlers"]["file_handler"]["level"] == "INFO"

    def test_override_log_levels_no_handlers_section(self):
        """Test overriding log levels when no handlers section exists."""
        config = {"loggers": {"root": {"level": "DEBUG"}}}
        result = override_log_levels(config, "INFO")

        # Should not raise an exception
        assert result["loggers"]["root"]["level"] == "INFO"


class TestSetupLogging:
    """Test cases for setup_logging function."""

    def test_setup_logging_custom_log_dir(self, tmp_path):
        """Test setup_logging with custom log directory."""
        config_file = tmp_path / "config.yaml"
        config = {
            "version": 1,
            "handlers": {
                "file_handler": {"class": "logging.FileHandler", "filename": "test.log"}
            },
            "loggers": {"root": {"level": "DEBUG", "handlers": ["file_handler"]}},
        }

        with open(config_file, "w") as f:
            yaml.dump(config, f)

        custom_log_dir = tmp_path / "custom_logs"

        with (
            patch(
                "hexapod.interface.logging.logging_utils.logging.config.dictConfig"
            ) as mock_dict_config,
            patch(
                "hexapod.interface.logging.logging_utils.logging.getLogger"
            ) as mock_get_logger,
            patch(
                "hexapod.interface.logging.logging_utils.rename_thread"
            ) as mock_rename_thread,
            patch(
                "hexapod.interface.logging.logging_utils.atexit.register"
            ) as mock_atexit,
        ):

            mock_logger = MagicMock()
            mock_handler = MagicMock()
            mock_handler.listener = MagicMock()
            mock_handler.listener._thread = MagicMock()
            mock_logger.handlers = [mock_handler]
            mock_get_logger.return_value = mock_logger

            setup_logging(log_dir=custom_log_dir, config_file=config_file)

            # Check that the log directory was created
            assert custom_log_dir.exists()

            # Check that the config was modified to use the custom log directory
            call_args = mock_dict_config.call_args[0][0]
            assert call_args["handlers"]["file_handler"]["filename"] == str(
                custom_log_dir / "test.log"
            )

    def test_setup_logging_custom_config_file(self, tmp_path):
        """Test setup_logging with custom config file."""
        config_file = tmp_path / "custom_config.yaml"
        config = {
            "version": 1,
            "handlers": {
                "file_handler": {
                    "class": "logging.FileHandler",
                    "filename": "custom.log",
                }
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config, f)

        with (
            patch(
                "hexapod.interface.logging.logging_utils.logging.config.dictConfig"
            ) as mock_dict_config,
            patch(
                "hexapod.interface.logging.logging_utils.logging.getLogger"
            ) as mock_get_logger,
            patch(
                "hexapod.interface.logging.logging_utils.rename_thread"
            ) as mock_rename_thread,
            patch(
                "hexapod.interface.logging.logging_utils.atexit.register"
            ) as mock_atexit,
        ):

            mock_logger = MagicMock()
            mock_handler = MagicMock()
            mock_handler.listener = MagicMock()
            mock_handler.listener._thread = MagicMock()
            mock_logger.handlers = [mock_handler]
            mock_get_logger.return_value = mock_logger

            setup_logging(config_file=config_file)

            # Check that dictConfig was called with the custom config
            mock_dict_config.assert_called_once()
            call_args = mock_dict_config.call_args[0][0]
            assert (
                call_args["handlers"]["file_handler"]["filename"] == "logs/custom.log"
            )

    def test_setup_logging_custom_log_level(self, tmp_path):
        """Test setup_logging with custom log level."""
        config_file = tmp_path / "config.yaml"
        config = {
            "version": 1,
            "loggers": {"root": {"level": "DEBUG"}},
            "handlers": {
                "file_handler": {"level": "DEBUG"},
                "stdout": {"level": "USER_INFO"},
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config, f)

        with (
            patch(
                "hexapod.interface.logging.logging_utils.logging.config.dictConfig"
            ) as mock_dict_config,
            patch(
                "hexapod.interface.logging.logging_utils.logging.getLogger"
            ) as mock_get_logger,
            patch(
                "hexapod.interface.logging.logging_utils.rename_thread"
            ) as mock_rename_thread,
            patch(
                "hexapod.interface.logging.logging_utils.atexit.register"
            ) as mock_atexit,
        ):

            mock_logger = MagicMock()
            mock_handler = MagicMock()
            mock_handler.listener = MagicMock()
            mock_handler.listener._thread = MagicMock()
            mock_logger.handlers = [mock_handler]
            mock_get_logger.return_value = mock_logger

            setup_logging(config_file=config_file, log_level="ERROR")

            # Check that log levels were overridden
            call_args = mock_dict_config.call_args[0][0]
            assert call_args["loggers"]["root"]["level"] == "ERROR"
            assert call_args["handlers"]["file_handler"]["level"] == "ERROR"
            # stdout should not be overridden
            assert call_args["handlers"]["stdout"]["level"] == "USER_INFO"

    def test_setup_logging_config_file_not_found(self, tmp_path):
        """Test setup_logging when config file doesn't exist."""
        non_existent_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(
            FileNotFoundError, match="Logging configuration file not found"
        ):
            setup_logging(config_file=non_existent_file)
