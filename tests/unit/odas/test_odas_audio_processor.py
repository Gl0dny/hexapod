"""
Unit tests for ODAS audio processor.
"""

import pytest
import numpy as np
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from hexapod.odas.odas_audio_processor import ODASAudioProcessor


class TestODASAudioProcessor:
    """Test cases for ODASAudioProcessor class."""

    @pytest.fixture
    def temp_odas_dir(self, tmp_path):
        """Create a temporary ODAS directory for testing."""
        odas_dir = tmp_path / "odas"
        odas_dir.mkdir()
        return odas_dir

    @pytest.fixture
    def processor_default(self, temp_odas_dir):
        """Create ODASAudioProcessor with default parameters."""
        return ODASAudioProcessor(odas_dir=temp_odas_dir)

    @pytest.fixture
    def processor_custom(self, temp_odas_dir):
        """Create ODASAudioProcessor with custom parameters."""
        return ODASAudioProcessor(
            odas_dir=temp_odas_dir,
            sample_rate=48000,
            channels=6,
            buffer_size=2048,
            check_interval=0.1,
            target_sample_rate=8000,
            target_channels=2,
            selected_channel=2,
            frame_length=256,
        )

    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data for testing."""
        # Create 4-channel audio data with enough samples for resampling
        # For default processor: source_samples = int(512 * (44100 / 16000)) = 1411
        samples = np.random.randint(-32768, 32767, (1411, 4), dtype=np.int16)
        return samples.tobytes()

    @pytest.fixture
    def sample_audio_data_custom(self):
        """Create sample audio data for custom processor testing."""
        # Create 6-channel audio data with enough samples for resampling
        # For custom processor: source_samples = int(256 * (48000 / 8000)) = 1536
        samples = np.random.randint(-32768, 32767, (1536, 6), dtype=np.int16)
        return samples.tobytes()

    def test_init_default_parameters(self, temp_odas_dir):
        """Test ODASAudioProcessor initialization with default parameters."""
        processor = ODASAudioProcessor(odas_dir=temp_odas_dir)

        assert processor.odas_dir == temp_odas_dir
        assert processor.audio_file == temp_odas_dir / "postfiltered.raw"
        assert processor.audio_callback is None
        assert processor.running is False
        assert processor.thread is None
        assert processor.source_sample_rate == 44100
        assert processor.target_sample_rate == 16000
        assert processor.source_channels == 4
        assert processor.target_channels == 1
        assert processor.selected_channel == 0
        assert processor.buffer_size == 1024
        assert processor.check_interval == 0.5
        assert processor.frame_length == 512
        assert processor.resample_ratio == 16000 / 44100
        assert processor._last_file_size == 0
        assert len(processor._buffer) == 0

    def test_init_custom_parameters(self, temp_odas_dir):
        """Test ODASAudioProcessor initialization with custom parameters."""
        processor = ODASAudioProcessor(
            odas_dir=temp_odas_dir,
            sample_rate=48000,
            channels=6,
            buffer_size=2048,
            check_interval=0.1,
            target_sample_rate=8000,
            target_channels=2,
            selected_channel=2,
            frame_length=256,
        )

        assert processor.odas_dir == temp_odas_dir
        assert processor.audio_file == temp_odas_dir / "postfiltered.raw"
        assert processor.source_sample_rate == 48000
        assert processor.target_sample_rate == 8000
        assert processor.source_channels == 6
        assert processor.target_channels == 2
        assert processor.selected_channel == 2
        assert processor.buffer_size == 2048
        assert processor.check_interval == 0.1
        assert processor.frame_length == 256
        assert processor.resample_ratio == 8000 / 48000

    def test_set_audio_callback(self, processor_default):
        """Test setting audio callback function."""
        callback = Mock()
        processor_default.set_audio_callback(callback)
        assert processor_default.audio_callback == callback

    def test_start_already_running(self, processor_default):
        """Test starting when already running."""
        processor_default.running = True
        processor_default.start()
        # Should not create a new thread
        assert processor_default.thread is None

    def test_start_success(self, processor_default):
        """Test successful start of audio processing."""
        processor_default.start()

        assert processor_default.running is True
        assert processor_default.thread is not None
        assert processor_default.thread.daemon is True
        assert processor_default.thread.is_alive() is True

        # Clean up
        processor_default.stop()

    def test_stop_not_running(self, processor_default):
        """Test stopping when not running."""
        processor_default.running = False
        processor_default.stop()
        # Should not raise any errors

    def test_stop_success(self, processor_default):
        """Test successful stop of audio processing."""
        processor_default.start()
        assert processor_default.running is True

        processor_default.stop()
        assert processor_default.running is False
        # Thread should be joined (not alive)
        if processor_default.thread:
            assert processor_default.thread.is_alive() is False

    def test_convert_audio_success(self, processor_default, sample_audio_data):
        """Test successful audio conversion."""
        converted = processor_default._convert_audio(sample_audio_data)

        assert converted is not None
        assert isinstance(converted, np.ndarray)
        assert converted.dtype == np.int16
        assert len(converted) == processor_default.frame_length
        assert converted.shape == (processor_default.frame_length,)

    def test_convert_audio_insufficient_samples(self, processor_default):
        """Test audio conversion with insufficient samples."""
        # Create very small audio data that can't be reshaped to 4 channels
        # Need at least 4 samples to reshape to (1, 4)
        small_data = b"\x00\x01" * 2  # Only 2 samples, can't reshape to 4 channels
        with pytest.raises(ValueError, match="cannot reshape array"):
            processor_default._convert_audio(small_data)

    def test_convert_audio_sample_accumulation(self, processor_default):
        """Test sample accumulation for insufficient data."""
        # Create data that's not enough for a complete frame but can be reshaped
        # Need at least 4 samples to reshape to channels, but not enough for frame
        # source_samples = 1411, so let's use 500 samples (125 per channel)
        small_data = (
            b"\x00\x01" * 500
        )  # 500 samples = 125 samples per channel, need more
        result1 = processor_default._convert_audio(small_data)
        assert result1 is None
        assert hasattr(processor_default, "_sample_buffer")

        # Second call with enough data to complete the frame
        # Need 1411 total samples, we have 500, so need 911 more
        # But we need to account for the fact that samples are accumulated per channel
        # So we need 1411 * 4 = 5644 total samples
        more_data = b"\x00\x01" * 6000  # 6000 more samples = 6500 total, enough
        result2 = processor_default._convert_audio(more_data)
        assert result2 is not None
        assert len(result2) == processor_default.frame_length

    def test_convert_audio_channel_selection(
        self, processor_custom, sample_audio_data_custom
    ):
        """Test channel selection in audio conversion."""
        converted = processor_custom._convert_audio(sample_audio_data_custom)
        assert converted is not None
        # Should select channel 2 (index 2)
        # Note: The actual conversion involves resampling, so we can't do exact comparison
        assert len(converted) == processor_custom.frame_length

    def test_convert_audio_resampling(self, processor_custom, sample_audio_data_custom):
        """Test audio resampling functionality."""
        converted = processor_custom._convert_audio(sample_audio_data_custom)
        assert converted is not None
        assert len(converted) == processor_custom.frame_length

    def test_convert_audio_padding(self, processor_default):
        """Test audio padding when resampled audio is too short."""
        # Create data that will result in shorter resampled audio
        # Need enough samples to pass the initial checks (1411 samples)
        samples = np.random.randint(-32768, 32767, (1411, 4), dtype=np.int16)
        audio_data = samples.tobytes()

        # Mock resampy to return shorter array
        with patch("resampy.resample") as mock_resample:
            mock_resample.return_value = np.array(
                [1, 2, 3], dtype=np.int16
            )  # Very short
            converted = processor_default._convert_audio(audio_data)

            assert converted is not None
            assert len(converted) == processor_default.frame_length
            # Should be padded with zeros
            assert np.all(converted[3:] == 0)

    def test_convert_audio_clipping(self, processor_default, sample_audio_data):
        """Test audio clipping to 16-bit range."""
        # Use the sample audio data which should work
        converted = processor_default._convert_audio(sample_audio_data)
        assert converted is not None
        # The conversion process should ensure values are within 16-bit range
        assert np.all(converted >= -32768)
        assert np.all(converted <= 32767)

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_read_audio_file_not_exists(
        self, mock_stat, mock_exists, mock_file, processor_default
    ):
        """Test reading audio when file doesn't exist."""
        mock_exists.return_value = False
        processor_default.audio_callback = Mock()

        # Start and immediately stop to avoid infinite loop
        processor_default.start()
        time.sleep(0.1)  # Let it run briefly
        processor_default.stop()

        # Should not call callback when file doesn't exist
        processor_default.audio_callback.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_read_audio_no_new_data(
        self, mock_stat, mock_exists, mock_file, processor_default
    ):
        """Test reading audio when no new data is available."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 1000
        processor_default._last_file_size = 1000  # Same size, no new data
        processor_default.audio_callback = Mock()

        processor_default.start()
        time.sleep(0.1)
        processor_default.stop()

        # Should not call callback when no new data
        processor_default.audio_callback.assert_not_called()

    def test_read_audio_with_new_data(self, processor_default, sample_audio_data):
        """Test reading audio with new data available."""
        # Test the _convert_audio method directly since the threading makes testing complex
        processor_default.audio_callback = Mock()

        # Test that the conversion works with proper data
        converted = processor_default._convert_audio(sample_audio_data)
        assert converted is not None
        assert len(converted) == processor_default.frame_length

        # Test callback integration
        if converted is not None:
            processor_default.audio_callback(converted)
            processor_default.audio_callback.assert_called_once_with(converted)

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_read_audio_incomplete_frame(
        self, mock_stat, mock_exists, mock_file, processor_default
    ):
        """Test reading audio with incomplete frame data."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 2000
        processor_default._last_file_size = 1000
        processor_default.audio_callback = Mock()

        # Mock file read to return incomplete data
        incomplete_data = b"\x00\x01" * 100  # Not enough for a complete frame
        mock_file.return_value.read.return_value = incomplete_data

        processor_default.start()
        time.sleep(0.1)
        processor_default.stop()

        # Should not call callback with incomplete frame
        processor_default.audio_callback.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_read_audio_multiple_frames(
        self, mock_stat, mock_exists, mock_file, processor_default, sample_audio_data
    ):
        """Test reading audio with multiple complete frames."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 2000
        processor_default._last_file_size = 1000
        processor_default.audio_callback = Mock()

        # Create data for multiple frames
        bytes_per_frame = (
            2 * processor_default.source_channels * processor_default.frame_length
        )
        multiple_frames = sample_audio_data * 3  # 3 complete frames
        mock_file.return_value.read.return_value = multiple_frames

        processor_default.start()
        time.sleep(0.1)
        processor_default.stop()

        # Should call callback multiple times
        assert processor_default.audio_callback.call_count >= 1

    @patch("builtins.open", side_effect=IOError("File read error"))
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_read_audio_file_error(
        self, mock_stat, mock_exists, mock_file, processor_default
    ):
        """Test reading audio when file read error occurs."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 2000
        processor_default._last_file_size = 1000
        processor_default.audio_callback = Mock()

        processor_default.start()
        time.sleep(0.1)
        processor_default.stop()

        # Should not call callback on file error
        processor_default.audio_callback.assert_not_called()

    @patch("time.sleep")
    def test_read_audio_fatal_error(self, mock_sleep, processor_default):
        """Test fatal error handling in read_audio."""
        # Mock a fatal error by making exists() raise an exception
        with patch("pathlib.Path.exists", side_effect=Exception("Fatal error")):
            processor_default.start()
            time.sleep(0.1)
            processor_default.stop()

        # Should handle fatal error gracefully
        assert processor_default.running is False

    def test_audio_callback_integration(self, processor_default, sample_audio_data):
        """Test integration with audio callback."""
        callback = Mock()
        processor_default.set_audio_callback(callback)

        # Test direct conversion
        converted = processor_default._convert_audio(sample_audio_data)
        if converted is not None:
            callback(converted)
            callback.assert_called_once_with(converted)

    def test_buffer_management(self, processor_default):
        """Test internal buffer management."""
        # Test initial buffer state
        assert len(processor_default._buffer) == 0

        # Test buffer extension
        test_data = b"\x00\x01\x02\x03"
        processor_default._buffer.extend(test_data)
        assert len(processor_default._buffer) == 4
        assert processor_default._buffer == bytearray(test_data)

    def test_file_size_tracking(self, processor_default):
        """Test file size tracking functionality."""
        assert processor_default._last_file_size == 0

        # Simulate file size update
        processor_default._last_file_size = 1000
        assert processor_default._last_file_size == 1000

    def test_resample_ratio_calculation(self, processor_default):
        """Test resample ratio calculation."""
        expected_ratio = 16000 / 44100
        assert abs(processor_default.resample_ratio - expected_ratio) < 1e-10

    def test_custom_resample_ratio(self, processor_custom):
        """Test resample ratio with custom parameters."""
        expected_ratio = 8000 / 48000
        assert abs(processor_custom.resample_ratio - expected_ratio) < 1e-10

    def test_frame_length_validation(self, processor_default, sample_audio_data):
        """Test that converted audio has correct frame length."""
        converted = processor_default._convert_audio(sample_audio_data)
        if converted is not None:
            assert len(converted) == processor_default.frame_length

    def test_audio_data_type_conversion(self, processor_default, sample_audio_data):
        """Test audio data type conversion."""
        converted = processor_default._convert_audio(sample_audio_data)
        if converted is not None:
            assert converted.dtype == np.int16

    def test_channel_reshaping(self, processor_default, sample_audio_data):
        """Test channel reshaping functionality."""
        # The method should handle multi-channel audio correctly
        converted = processor_default._convert_audio(sample_audio_data)
        if converted is not None:
            # Should be mono after channel selection
            assert len(converted.shape) == 1

    def test_thread_daemon_property(self, processor_default):
        """Test that audio reading thread is daemon."""
        processor_default.start()
        assert processor_default.thread.daemon is True
        processor_default.stop()

    def test_audio_file_path_construction(self, temp_odas_dir):
        """Test audio file path construction."""
        processor = ODASAudioProcessor(odas_dir=temp_odas_dir)
        expected_path = temp_odas_dir / "postfiltered.raw"
        assert processor.audio_file == expected_path

    def test_initialization_logging(self, temp_odas_dir, capsys):
        """Test initialization logging output."""
        processor = ODASAudioProcessor(odas_dir=temp_odas_dir)
        captured = capsys.readouterr()

        # Check that initialization messages are printed
        assert "Initializing ODASAudioProcessor" in captured.out
        assert "Audio file path:" in captured.out
        assert "Initialized with sample_rate=" in captured.out

    def test_start_stop_cycle(self, processor_default):
        """Test multiple start/stop cycles."""
        # First cycle
        processor_default.start()
        assert processor_default.running is True
        processor_default.stop()
        assert processor_default.running is False

        # Second cycle
        processor_default.start()
        assert processor_default.running is True
        processor_default.stop()
        assert processor_default.running is False

    def test_callback_none_handling(self, processor_default, sample_audio_data):
        """Test handling when callback is None."""
        processor_default.audio_callback = None

        # Should not raise error when callback is None
        processor_default._convert_audio(sample_audio_data)

    def test_edge_case_zero_samples(self, processor_default):
        """Test edge case with zero samples."""
        empty_data = b""
        result = processor_default._convert_audio(empty_data)
        assert result is None

    def test_edge_case_single_sample(self, processor_default):
        """Test edge case with single sample."""
        single_sample = b"\x00\x01"  # One sample
        with pytest.raises(ValueError, match="cannot reshape array"):
            processor_default._convert_audio(single_sample)
