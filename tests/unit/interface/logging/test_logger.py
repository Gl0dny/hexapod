"""
Unit tests for custom logger functionality.
"""

import pytest
import logging
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from hexapod.interface.logging.logger import (
    CustomLogger,
    get_custom_logger,
    MyJSONFormatter,
    VerboseFormatter,
    ColoredTerminalFormatter,
    USER_INFO_LEVEL,
    ODAS_USER_INFO_LEVEL,
    GAMEPAD_MODE_INFO_LEVEL,
)


class TestCustomLogger:
    """Test cases for CustomLogger class."""

    def test_user_info_method(self):
        """Test user_info logging method."""
        logger = CustomLogger("test_logger")

        with patch.object(logger, "_log") as mock_log:
            logger.user_info("Test user info message")

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == USER_INFO_LEVEL
            assert call_args[0][1] == "Test user info message"
            assert call_args[1]["stacklevel"] == 2

    def test_odas_user_info_method(self):
        """Test odas_user_info logging method."""
        logger = CustomLogger("test_logger")

        with patch.object(logger, "_log") as mock_log:
            logger.odas_user_info("Test ODAS user info message")

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == ODAS_USER_INFO_LEVEL
            assert call_args[0][1] == "Test ODAS user info message"
            assert call_args[1]["stacklevel"] == 2

    def test_gamepad_mode_info_method(self):
        """Test gamepad_mode_info logging method."""
        logger = CustomLogger("test_logger")

        with patch.object(logger, "_log") as mock_log:
            logger.gamepad_mode_info("Test gamepad mode info message")

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == GAMEPAD_MODE_INFO_LEVEL
            assert call_args[0][1] == "Test gamepad mode info message"
            assert call_args[1]["stacklevel"] == 2

    def test_user_info_with_args(self):
        """Test user_info method with additional arguments."""
        logger = CustomLogger("test_logger")

        with patch.object(logger, "_log") as mock_log:
            logger.user_info("Test message %s %d", "arg1", 42)

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == USER_INFO_LEVEL
            assert call_args[0][1] == "Test message %s %d"
            assert call_args[0][2] == ("arg1", 42)

    def test_user_info_with_kwargs(self):
        """Test user_info method with keyword arguments."""
        logger = CustomLogger("test_logger")

        with patch.object(logger, "_log") as mock_log:
            logger.user_info("Test message", extra={"key": "value"})

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == USER_INFO_LEVEL
            assert call_args[0][1] == "Test message"
            assert call_args[1]["extra"] == {"key": "value"}

    def test_user_info_level_check(self):
        """Test user_info method respects level checking."""
        logger = CustomLogger("test_logger")
        logger.setLevel(logging.ERROR)  # Set level higher than USER_INFO

        with patch.object(logger, "_log") as mock_log:
            logger.user_info("This should not be logged")

            # Should not call _log because level is too high
            mock_log.assert_not_called()

    def test_odas_user_info_level_check(self):
        """Test odas_user_info method respects level checking."""
        logger = CustomLogger("test_logger")
        logger.setLevel(logging.CRITICAL)  # Set level higher than ODAS_USER_INFO

        with patch.object(logger, "_log") as mock_log:
            logger.odas_user_info("This should not be logged")

            # Should not call _log because level is too high
            mock_log.assert_not_called()

    def test_gamepad_mode_info_level_check(self):
        """Test gamepad_mode_info method respects level checking."""
        logger = CustomLogger("test_logger")
        logger.setLevel(logging.CRITICAL)  # Set level higher than GAMEPAD_MODE_INFO

        with patch.object(logger, "_log") as mock_log:
            logger.gamepad_mode_info("This should not be logged")

            # Should not call _log because level is too high
            mock_log.assert_not_called()


class TestGetCustomLogger:
    """Test cases for get_custom_logger function."""

    def test_get_custom_logger_returns_custom_logger(self):
        """Test that get_custom_logger returns a CustomLogger instance."""
        with (
            patch(
                "hexapod.interface.logging.logger.logging.setLoggerClass"
            ) as mock_set_class,
            patch(
                "hexapod.interface.logging.logger.logging.getLogger"
            ) as mock_get_logger,
        ):

            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = get_custom_logger("test_name")

            mock_set_class.assert_called_once_with(CustomLogger)
            mock_get_logger.assert_called_once_with("test_name")
            assert result == mock_logger

    def test_get_custom_logger_with_different_names(self):
        """Test get_custom_logger with different logger names."""
        with (
            patch("hexapod.interface.logging.logger.logging.setLoggerClass"),
            patch(
                "hexapod.interface.logging.logger.logging.getLogger"
            ) as mock_get_logger,
        ):

            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Test with different names
            names = ["test1", "test2", "main_logger", "odas_logger"]
            for name in names:
                result = get_custom_logger(name)
                mock_get_logger.assert_called_with(name)
                assert result == mock_logger


class TestMyJSONFormatter:
    """Test cases for MyJSONFormatter class."""

    def test_init_default_fmt_keys(self):
        """Test MyJSONFormatter initialization with default fmt_keys."""
        formatter = MyJSONFormatter()
        assert formatter.fmt_keys == {}

    def test_init_custom_fmt_keys(self):
        """Test MyJSONFormatter initialization with custom fmt_keys."""
        custom_keys = {"level": "levelname", "message": "message"}
        formatter = MyJSONFormatter(fmt_keys=custom_keys)
        assert formatter.fmt_keys == custom_keys

    def test_format_basic_record(self):
        """Test formatting a basic log record."""
        formatter = MyJSONFormatter()

        # Create a mock log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.created = 1640995200.0  # 2022-01-01 00:00:00 UTC

        result = formatter.format(record)
        parsed_result = json.loads(result)

        assert parsed_result["message"] == "Test message"
        assert "timestamp" in parsed_result
        assert parsed_result["timestamp"] == "2022-01-01T00:00:00+00:00"

    def test_format_with_custom_fmt_keys(self):
        """Test formatting with custom format keys."""
        custom_keys = {"level": "levelname", "logger": "name", "message": "message"}
        formatter = MyJSONFormatter(fmt_keys=custom_keys)

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.created = 1640995200.0

        result = formatter.format(record)
        parsed_result = json.loads(result)

        assert parsed_result["level"] == "INFO"
        assert parsed_result["logger"] == "test_logger"
        assert parsed_result["message"] == "Test message"

    def test_format_with_exception_info(self):
        """Test formatting with exception information."""
        formatter = MyJSONFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Test error",
            args=(),
            exc_info=None,
        )
        record.created = 1640995200.0

        # Mock exception info
        try:
            raise ValueError("Test exception")
        except ValueError:
            record.exc_info = (ValueError, ValueError("Test exception"), None)

        result = formatter.format(record)
        parsed_result = json.loads(result)

        assert parsed_result["message"] == "Test error"
        assert "exc_info" in parsed_result
        assert "ValueError: Test exception" in parsed_result["exc_info"]

    def test_format_with_stack_info(self):
        """Test formatting with stack information."""
        formatter = MyJSONFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Test error",
            args=(),
            exc_info=None,
        )
        record.created = 1640995200.0
        record.stack_info = "Stack trace information"

        result = formatter.format(record)
        parsed_result = json.loads(result)

        assert parsed_result["message"] == "Test error"
        assert parsed_result["stack_info"] == "Stack trace information"

    def test_prepare_log_dict(self):
        """Test _prepare_log_dict method."""
        formatter = MyJSONFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.created = 1640995200.0

        result = formatter._prepare_log_dict(record)

        assert result["message"] == "Test message"
        assert result["timestamp"] == "2022-01-01T00:00:00+00:00"
        assert "exc_info" not in result
        assert "stack_info" not in result


class TestVerboseFormatter:
    """Test cases for VerboseFormatter class."""

    def test_init_default_format(self):
        """Test VerboseFormatter initialization with default format."""
        formatter = VerboseFormatter()

        # Check that the default format is set correctly
        expected_fmt = "[%(levelname)s - %(module)s - %(threadName)s - %(funcName)s - Line: %(lineno)-4d] - %(asctime)s - %(message)s"
        assert formatter._fmt == expected_fmt

    def test_init_custom_format(self):
        """Test VerboseFormatter initialization with custom format."""
        custom_fmt = "%(levelname)s: %(message)s"
        formatter = VerboseFormatter(fmt=custom_fmt)
        assert formatter._fmt == custom_fmt

    def test_init_custom_date_format(self):
        """Test VerboseFormatter initialization with custom date format."""
        custom_datefmt = "%Y-%m-%d"
        formatter = VerboseFormatter(datefmt=custom_datefmt)
        assert formatter.datefmt == custom_datefmt

    def test_init_custom_style(self):
        """Test VerboseFormatter initialization with custom style."""
        # Use a format string compatible with the style
        custom_fmt = "[{levelname} - {module} - {threadName} - {funcName} - Line: {lineno:4d}] - {asctime} - {message}"
        formatter = VerboseFormatter(fmt=custom_fmt, style="{")
        assert formatter._style._fmt == formatter._fmt

    def test_init_validate_false(self):
        """Test VerboseFormatter initialization with validation disabled."""
        formatter = VerboseFormatter(validate=False)
        # Should not raise an exception even with invalid format
        assert formatter is not None

    def test_format_record(self):
        """Test formatting a log record."""
        formatter = VerboseFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.threadName = "MainThread"
        record.funcName = "test_function"
        record.created = 1640995200.0

        result = formatter.format(record)

        # Check that the result contains expected components
        assert "INFO" in result
        assert "test_module" in result
        assert "MainThread" in result
        assert "test_function" in result
        assert "Line: 10" in result
        assert "Test message" in result

    def test_format_record_spacing(self):
        """Test that format method applies proper spacing."""
        formatter = VerboseFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "very_long_module_name_that_exceeds_normal_length"
        record.threadName = "VeryLongThreadNameThatExceedsNormalLength"
        record.funcName = "very_long_function_name_that_exceeds_normal_length"
        record.created = 1640995200.0

        result = formatter.format(record)

        # Check that spacing is applied (centered with 30 characters)
        lines = result.split("\n")
        for line in lines:
            if "test_module" in line or "very_long_module_name" in line:
                # The module name should be centered in a 30-character field
                assert len(line) > 30  # Should be padded


class TestColoredTerminalFormatter:
    """Test cases for ColoredTerminalFormatter class."""

    def test_init_ansi_colors(self):
        """Test that ANSI colors are properly defined."""
        formatter = ColoredTerminalFormatter()

        # Check that all expected colors are defined
        expected_colors = [
            "BLUE",
            "GREEN",
            "CYAN",
            "YELLOW",
            "RED",
            "BOLD_RED",
            "MAGENTA",
            "ORANGE",
            "PINK",
            "PURPLE",
        ]
        for color in expected_colors:
            assert color in formatter.ANSI_COLORS
            assert formatter.ANSI_COLORS[color].startswith("\033[")

    def test_init_reset_color(self):
        """Test that reset color is properly defined."""
        formatter = ColoredTerminalFormatter()
        assert formatter.RESET_COLOR == "\033[0m"

    def test_init_format_string(self):
        """Test that format string is properly defined."""
        formatter = ColoredTerminalFormatter()
        expected_fmt = "[{levelname:^9} - {module:^30} - {asctime}] - {message}"
        assert formatter.FMT == expected_fmt

    def test_init_formats_mapping(self):
        """Test that formats mapping includes all expected levels."""
        formatter = ColoredTerminalFormatter()

        # Check that all expected levels are in the formats mapping
        expected_levels = [
            logging.DEBUG,
            logging.INFO,
            USER_INFO_LEVEL,
            ODAS_USER_INFO_LEVEL,
            GAMEPAD_MODE_INFO_LEVEL,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]
        for level in expected_levels:
            assert level in formatter.FORMATS

    def test_format_debug_level(self):
        """Test formatting DEBUG level messages."""
        formatter = ColoredTerminalFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=10,
            msg="Debug message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.created = 1640995200.0

        result = formatter.format(record)

        # DEBUG should use the base format without colors
        assert "DEBUG" in result
        assert "Debug message" in result
        assert "\033[" not in result  # No ANSI color codes

    def test_format_info_level(self):
        """Test formatting INFO level messages."""
        formatter = ColoredTerminalFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Info message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.created = 1640995200.0

        result = formatter.format(record)

        # INFO should use green color
        assert "INFO" in result
        assert "Info message" in result
        assert formatter.ANSI_COLORS["GREEN"] in result
        assert formatter.RESET_COLOR in result

    def test_format_user_info_level(self):
        """Test formatting USER_INFO level messages."""
        formatter = ColoredTerminalFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=USER_INFO_LEVEL,
            pathname="test.py",
            lineno=10,
            msg="User info message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.created = 1640995200.0

        result = formatter.format(record)

        # USER_INFO should use cyan color
        assert "USER_INFO" in result
        assert "User info message" in result
        assert formatter.ANSI_COLORS["CYAN"] in result
        assert formatter.RESET_COLOR in result

    def test_format_odas_user_info_level(self):
        """Test formatting ODAS_USER_INFO level messages."""
        formatter = ColoredTerminalFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=ODAS_USER_INFO_LEVEL,
            pathname="test.py",
            lineno=10,
            msg="ODAS user info message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.created = 1640995200.0

        result = formatter.format(record)

        # ODAS_USER_INFO should use green color
        assert "ODAS_USER_INFO" in result
        assert "ODAS user info message" in result
        assert formatter.ANSI_COLORS["GREEN"] in result
        assert formatter.RESET_COLOR in result

    def test_format_gamepad_mode_info_level(self):
        """Test formatting GAMEPAD_MODE_INFO level messages."""
        formatter = ColoredTerminalFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=GAMEPAD_MODE_INFO_LEVEL,
            pathname="test.py",
            lineno=10,
            msg="Gamepad mode info message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.created = 1640995200.0

        result = formatter.format(record)

        # GAMEPAD_MODE_INFO should use purple color
        assert "GAMEPAD_MODE_INFO" in result
        assert "Gamepad mode info message" in result
        assert formatter.ANSI_COLORS["PURPLE"] in result
        assert formatter.RESET_COLOR in result

    def test_format_warning_level(self):
        """Test formatting WARNING level messages."""
        formatter = ColoredTerminalFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname="test.py",
            lineno=10,
            msg="Warning message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.created = 1640995200.0

        result = formatter.format(record)

        # WARNING should use yellow color
        assert "WARNING" in result
        assert "Warning message" in result
        assert formatter.ANSI_COLORS["YELLOW"] in result
        assert formatter.RESET_COLOR in result

    def test_format_error_level(self):
        """Test formatting ERROR level messages."""
        formatter = ColoredTerminalFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.created = 1640995200.0

        result = formatter.format(record)

        # ERROR should use red color
        assert "ERROR" in result
        assert "Error message" in result
        assert formatter.ANSI_COLORS["RED"] in result
        assert formatter.RESET_COLOR in result

    def test_format_critical_level(self):
        """Test formatting CRITICAL level messages."""
        formatter = ColoredTerminalFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.CRITICAL,
            pathname="test.py",
            lineno=10,
            msg="Critical message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.created = 1640995200.0

        result = formatter.format(record)

        # CRITICAL should use bold red color
        assert "CRITICAL" in result
        assert "Critical message" in result
        assert formatter.ANSI_COLORS["BOLD_RED"] in result
        assert formatter.RESET_COLOR in result

    def test_format_unknown_level(self):
        """Test formatting unknown level messages."""
        formatter = ColoredTerminalFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=999,  # Unknown level
            pathname="test.py",
            lineno=10,
            msg="Unknown level message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.created = 1640995200.0

        result = formatter.format(record)

        # Unknown level should use base format without colors
        assert "Unknown level message" in result
        assert "\033[" not in result  # No ANSI color codes

    def test_format_with_style_override(self):
        """Test that format method uses the correct style."""
        formatter = ColoredTerminalFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.created = 1640995200.0

        result = formatter.format(record)

        # Should contain the formatted message with color codes
        assert "INFO" in result
        assert "test_module" in result
        assert "Test message" in result


class TestLoggingLevels:
    """Test cases for custom logging levels."""

    def test_custom_levels_are_registered(self):
        """Test that custom logging levels are properly registered."""
        # Check that custom levels are added to logging module
        assert hasattr(logging, "USER_INFO")
        assert hasattr(logging, "ODAS_USER_INFO")
        assert hasattr(logging, "GAMEPAD_MODE_INFO")

        # Check that level names are registered
        assert logging.getLevelName(USER_INFO_LEVEL) == "USER_INFO"
        assert logging.getLevelName(ODAS_USER_INFO_LEVEL) == "ODAS_USER_INFO"
        assert logging.getLevelName(GAMEPAD_MODE_INFO_LEVEL) == "GAMEPAD_MODE_INFO"

    def test_custom_level_values(self):
        """Test that custom level values are correct."""
        assert USER_INFO_LEVEL == 25
        assert ODAS_USER_INFO_LEVEL == 26
        assert GAMEPAD_MODE_INFO_LEVEL == 27

    def test_custom_levels_in_logging_module(self):
        """Test that custom levels are accessible in logging module."""
        assert logging.USER_INFO == USER_INFO_LEVEL
        assert logging.ODAS_USER_INFO == ODAS_USER_INFO_LEVEL
        assert logging.GAMEPAD_MODE_INFO == GAMEPAD_MODE_INFO_LEVEL
