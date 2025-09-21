"""
Shared test configuration and fixtures for the hexapod project.
"""

import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Mock ALL external dependencies BEFORE any imports
import unittest.mock as mock

# Mock external dependencies that are not available in test environment
sys.modules["dotenv"] = mock.MagicMock()
sys.modules["serial"] = mock.MagicMock()
sys.modules["icm20948"] = mock.MagicMock()
sys.modules["RPi"] = mock.MagicMock()
sys.modules["RPi.GPIO"] = mock.MagicMock()
sys.modules["smbus2"] = mock.MagicMock()
sys.modules["spidev"] = mock.MagicMock()
sys.modules["gpiozero"] = mock.MagicMock()
sys.modules["gpiozero.pins"] = mock.MagicMock()
sys.modules["gpiozero.pins.rpigpio"] = mock.MagicMock()
sys.modules["gpiozero.pins.rpigpio.RPiGPIOFactory"] = mock.MagicMock()
sys.modules["pyaudio"] = mock.MagicMock()
sys.modules["pygame"] = mock.MagicMock()
sys.modules["pvporcupine"] = mock.MagicMock()
sys.modules["pvrhino"] = mock.MagicMock()
sys.modules["picovoice"] = mock.MagicMock()
sys.modules["paramiko"] = mock.MagicMock()
sys.modules["resampy"] = mock.MagicMock()
sys.modules["sounddevice"] = mock.MagicMock()
sys.modules["dualsense_controller"] = mock.MagicMock()

# Now import pytest and other modules
import pytest
