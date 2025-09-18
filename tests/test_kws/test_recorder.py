import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def recorder_module():
    """Import the real recorder module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "recorder_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/kws/recorder.py"
    )
    recorder_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recorder_module)
    return recorder_module


class TestRecorder:
    """Test the Recorder class from recorder.py"""

    def test_recorder_class_exists(self, recorder_module):
        """Test that Recorder class exists."""
        assert hasattr(recorder_module, 'Recorder')
        assert callable(recorder_module.Recorder)

    def test_recorder_initialization(self, recorder_module):
        """Test Recorder initialization."""
        recorder = recorder_module.Recorder()
        
        # Verify initialization
        assert hasattr(recorder, 'is_recording')
        assert hasattr(recorder, 'recordings_dir')
        assert recorder.is_recording is False

    def test_recorder_methods_exist(self, recorder_module):
        """Test that Recorder has required methods."""
        Recorder = recorder_module.Recorder
        
        # Test that required methods exist
        required_methods = ['start_recording', 'stop_recording']
        
        for method_name in required_methods:
            assert hasattr(Recorder, method_name), f"Recorder should have {method_name} method"

    def test_start_recording(self, recorder_module):
        """Test start_recording method."""
        recorder = recorder_module.Recorder()
        recorder.start_recording()
        
        # Verify recording state
        assert recorder.is_recording is True

    def test_stop_recording(self, recorder_module):
        """Test stop_recording method."""
        recorder = recorder_module.Recorder()
        recorder.start_recording()
        recorder.stop_recording()
        
        # Verify recording state
        assert recorder.is_recording is False
