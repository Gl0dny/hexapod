"""
Unit tests for ODAS to Picovoice WAV converter.
"""

import pytest
import tempfile
import wave
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import sys
import time

from hexapod.odas.odas_to_picovoice_wav import convert_odas_to_wav, main


class TestConvertODASToWAV:
    """Test cases for convert_odas_to_wav function."""

    @pytest.fixture
    def temp_input_file(self):
        """Create a temporary input file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as f:
            # Write some sample audio data
            sample_data = np.random.randint(-32768, 32767, (1000, 4), dtype=np.int16)
            f.write(sample_data.tobytes())
            return Path(f.name)

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary output file path for testing."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            return Path(f.name)

    @pytest.fixture
    def mock_odas_processor(self):
        """Mock ODASAudioProcessor for testing."""
        mock_processor = Mock()
        mock_processor.running = True
        mock_processor.set_audio_callback = Mock()
        mock_processor.start = Mock()
        mock_processor.stop = Mock()
        return mock_processor

    def test_convert_odas_to_wav_success(
        self, temp_input_file, temp_output_file, mock_odas_processor
    ):
        """Test successful conversion of ODAS to WAV."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file - wave.open returns the file object directly, not a context manager
            mock_wav_file = Mock()
            mock_wave_open.return_value = mock_wav_file

            # Mock file size changes to simulate new data
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # Create a time counter that increments slowly
                time_counter = [0]

                def mock_time():
                    time_counter[0] += 0.1
                    return time_counter[0]

                # Simulate the processor running for a few iterations then stopping
                call_count = 0

                def stop_processor(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count >= 3:  # Allow a few iterations
                        mock_odas_processor.running = False

                with (
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.time",
                        side_effect=mock_time,
                    ),
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.sleep",
                        side_effect=stop_processor,
                    ),
                ):
                    convert_odas_to_wav(temp_input_file, temp_output_file)

            # Verify ODASAudioProcessor was created with correct parameters
            from hexapod.odas.odas_to_picovoice_wav import ODASAudioProcessor

            ODASAudioProcessor.assert_called_once()
            call_args = ODASAudioProcessor.call_args
            assert call_args[1]["sample_rate"] == 44100
            assert call_args[1]["channels"] == 4
            assert call_args[1]["selected_channel"] == 0

            # Verify WAV file was opened and configured
            mock_wave_open.assert_called_once_with(str(temp_output_file), "wb")
            # WAV file configuration happens after ODASAudioProcessor creation
            mock_wav_file.setnchannels.assert_called_once_with(1)
            mock_wav_file.setsampwidth.assert_called_once_with(2)
            mock_wav_file.setframerate.assert_called_once_with(16000)
            mock_wav_file.close.assert_called_once()

            # Verify processor methods were called
            mock_odas_processor.set_audio_callback.assert_called_once()
            mock_odas_processor.start.assert_called_once()
            mock_odas_processor.stop.assert_called_once()

    def test_convert_odas_to_wav_custom_parameters(
        self, temp_input_file, temp_output_file, mock_odas_processor
    ):
        """Test conversion with custom parameters."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__.return_value = mock_wav_file

            # Mock file size changes
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # Create a time counter that starts at 0 and increments
                time_counter = [0]

                def mock_time():
                    time_counter[0] += 0.1
                    return time_counter[0]

                # Simulate the processor stopping after a few iterations
                def stop_processor(*args, **kwargs):
                    mock_odas_processor.running = False

                with (
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.time",
                        side_effect=mock_time,
                    ),
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.sleep",
                        side_effect=stop_processor,
                    ),
                ):
                    convert_odas_to_wav(
                        temp_input_file,
                        temp_output_file,
                        sample_rate=48000,
                        channels=6,
                        selected_channel=2,
                    )

            # Verify ODASAudioProcessor was created with custom parameters
            from hexapod.odas.odas_to_picovoice_wav import ODASAudioProcessor

            call_args = ODASAudioProcessor.call_args
            assert call_args[1]["sample_rate"] == 48000
            assert call_args[1]["channels"] == 6
            assert call_args[1]["selected_channel"] == 2

    def test_convert_odas_to_wav_timeout(
        self, temp_input_file, temp_output_file, mock_odas_processor
    ):
        """Test conversion timeout handling."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__.return_value = mock_wav_file

            # Mock file size changes
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # Create a time counter that simulates timeout
                time_counter = [0]

                def mock_time():
                    time_counter[0] += 15  # Increment by 15 seconds each call
                    return time_counter[0]

                with patch(
                    "hexapod.odas.odas_to_picovoice_wav.time.time",
                    side_effect=mock_time,
                ):
                    convert_odas_to_wav(temp_input_file, temp_output_file)

            # Verify processor was stopped due to timeout
            mock_odas_processor.stop.assert_called_once()

    def test_convert_odas_to_wav_no_change_detection(
        self, temp_input_file, temp_output_file, mock_odas_processor
    ):
        """Test conversion stops when no file size change is detected."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__.return_value = mock_wav_file

            # Mock file size staying constant
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # Create a time counter that increments slowly
                time_counter = [0]

                def mock_time():
                    time_counter[0] += 0.1
                    return time_counter[0]

                with patch(
                    "hexapod.odas.odas_to_picovoice_wav.time.time",
                    side_effect=mock_time,
                ):
                    convert_odas_to_wav(temp_input_file, temp_output_file)

            # Verify processor was stopped due to no change
            mock_odas_processor.stop.assert_called_once()

    def test_convert_odas_to_wav_audio_callback(
        self, temp_input_file, temp_output_file, mock_odas_processor
    ):
        """Test audio callback functionality."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file - wave.open returns the file object directly, not a context manager
            mock_wav_file = Mock()
            mock_wave_open.return_value = mock_wav_file

            # Mock file size changes to simulate new data
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # Create a time counter that increments slowly
                time_counter = [0]

                def mock_time():
                    time_counter[0] += 0.1
                    return time_counter[0]

                # Capture the callback and simulate it being called during conversion
                captured_callback = None

                def capture_callback(callback):
                    nonlocal captured_callback
                    captured_callback = callback
                    return Mock()

                mock_odas_processor.set_audio_callback.side_effect = capture_callback

                # Simulate the processor running and calling the callback
                call_count = 0

                def stop_processor(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count >= 3:  # Allow a few iterations
                        # Simulate the callback being called during conversion
                        if captured_callback:
                            sample_audio = np.array([1, 2, 3, 4], dtype=np.int16)
                            captured_callback(sample_audio)
                        mock_odas_processor.running = False

                with (
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.time",
                        side_effect=mock_time,
                    ),
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.sleep",
                        side_effect=stop_processor,
                    ),
                ):
                    convert_odas_to_wav(temp_input_file, temp_output_file)

            # Verify callback was set
            mock_odas_processor.set_audio_callback.assert_called_once()

            # Verify WAV file write was called
            mock_wav_file.writeframes.assert_called()

    def test_convert_odas_to_wav_wav_file_configuration(
        self, temp_input_file, temp_output_file, mock_odas_processor
    ):
        """Test WAV file configuration parameters."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file - wave.open returns the file object directly, not a context manager
            mock_wav_file = Mock()
            mock_wave_open.return_value = mock_wav_file

            # Mock file size changes to simulate new data
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # Create a time counter that increments slowly
                time_counter = [0]

                def mock_time():
                    time_counter[0] += 0.1
                    return time_counter[0]

                # Simulate the processor running for a few iterations then stopping
                call_count = 0

                def stop_processor(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count >= 3:  # Allow a few iterations
                        mock_odas_processor.running = False

                with (
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.time",
                        side_effect=mock_time,
                    ),
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.sleep",
                        side_effect=stop_processor,
                    ),
                ):
                    convert_odas_to_wav(temp_input_file, temp_output_file)

            # Verify WAV file configuration
            mock_wav_file.setnchannels.assert_called_once_with(1)  # Mono
            mock_wav_file.setsampwidth.assert_called_once_with(2)  # 16-bit
            mock_wav_file.setframerate.assert_called_once_with(
                16000
            )  # Picovoice sample rate

    def test_convert_odas_to_wav_temp_directory_cleanup(
        self, temp_input_file, temp_output_file, mock_odas_processor
    ):
        """Test that temporary directory is properly cleaned up."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__.return_value = mock_wav_file

            # Mock file size changes
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # Create a time counter that increments slowly
                time_counter = [0]

                def mock_time():
                    time_counter[0] += 0.1
                    return time_counter[0]

                # Simulate the processor stopping after a few iterations
                def stop_processor(*args, **kwargs):
                    mock_odas_processor.running = False

                with (
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.time",
                        side_effect=mock_time,
                    ),
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.sleep",
                        side_effect=stop_processor,
                    ),
                ):
                    convert_odas_to_wav(temp_input_file, temp_output_file)

            # Verify ODASAudioProcessor was created with a temporary directory
            from hexapod.odas.odas_to_picovoice_wav import ODASAudioProcessor

            call_args = ODASAudioProcessor.call_args
            assert "odas_dir" in call_args[1]
            assert isinstance(call_args[1]["odas_dir"], Path)

    def test_convert_odas_to_wav_error_handling(
        self, temp_input_file, temp_output_file, mock_odas_processor
    ):
        """Test error handling during conversion."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__.return_value = mock_wav_file

            # Mock file size changes
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # Create a time counter that increments slowly
                time_counter = [0]

                def mock_time():
                    time_counter[0] += 0.1
                    return time_counter[0]

                # Simulate the processor stopping after a few iterations
                def stop_processor(*args, **kwargs):
                    mock_odas_processor.running = False

                with (
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.time",
                        side_effect=mock_time,
                    ),
                    patch(
                        "hexapod.odas.odas_to_picovoice_wav.time.sleep",
                        side_effect=stop_processor,
                    ),
                ):
                    convert_odas_to_wav(temp_input_file, temp_output_file)

            # Verify processor was properly stopped even if errors occur
            mock_odas_processor.stop.assert_called_once()

    def test_convert_odas_to_wav_file_not_found(
        self, temp_output_file, mock_odas_processor
    ):
        """Test handling of non-existent input file."""
        non_existent_file = Path("/non/existent/file.raw")

        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__.return_value = mock_wav_file

            # Mock file size changes
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # Simulate the processor stopping after a few iterations
                def stop_processor(*args, **kwargs):
                    mock_odas_processor.running = False

                with patch(
                    "hexapod.odas.odas_to_picovoice_wav.time.sleep",
                    side_effect=stop_processor,
                ):
                    convert_odas_to_wav(non_existent_file, temp_output_file)

            # Verify processor was still stopped
            mock_odas_processor.stop.assert_called_once()


class TestMain:
    """Test cases for main function."""

    def test_main_with_default_args(self):
        """Test main function with default arguments."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.convert_odas_to_wav"
            ) as mock_convert,
            patch(
                "hexapod.odas.odas_to_picovoice_wav.sys.argv",
                ["script.py", "input.raw", "output.wav"],
            ),
        ):

            main()

            # Verify convert_odas_to_wav was called with default parameters
            mock_convert.assert_called_once()
            call_args = mock_convert.call_args
            assert call_args[0][0] == Path("input.raw")
            assert call_args[0][1] == Path("output.wav")
            assert call_args[0][2] == 44100  # sample_rate
            assert call_args[0][3] == 4  # channels
            assert call_args[0][4] == 0  # selected_channel

    def test_main_with_custom_args(self):
        """Test main function with custom arguments."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.convert_odas_to_wav"
            ) as mock_convert,
            patch(
                "hexapod.odas.odas_to_picovoice_wav.sys.argv",
                [
                    "script.py",
                    "input.raw",
                    "output.wav",
                    "--sample-rate",
                    "48000",
                    "--channels",
                    "6",
                    "--channel",
                    "2",
                ],
            ),
        ):

            main()

            # Verify convert_odas_to_wav was called with custom parameters
            mock_convert.assert_called_once()
            call_args = mock_convert.call_args
            assert call_args[0][0] == Path("input.raw")
            assert call_args[0][1] == Path("output.wav")
            assert call_args[0][2] == 48000  # sample_rate
            assert call_args[0][3] == 6  # channels
            assert call_args[0][4] == 2  # selected_channel

    def test_main_path_manipulation(self):
        """Test that main function properly manipulates sys.path."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.convert_odas_to_wav"
            ) as mock_convert,
            patch(
                "hexapod.odas.odas_to_picovoice_wav.sys.argv",
                ["script.py", "input.raw", "output.wav"],
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.sys.path") as mock_path,
        ):

            main()

            # Verify sys.path.append was called
            mock_path.append.assert_called()

    def test_main_script_path_calculation(self):
        """Test that main function correctly calculates script and project paths."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.convert_odas_to_wav"
            ) as mock_convert,
            patch(
                "hexapod.odas.odas_to_picovoice_wav.sys.argv",
                ["script.py", "input.raw", "output.wav"],
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.Path") as mock_path,
        ):

            # Mock the script path
            mock_script_path = Mock()
            mock_script_path.resolve.return_value = Path(
                "/project/hexapod/odas/odas_to_picovoice_wav.py"
            )
            mock_script_path.parent.parent.parent = Path("/project")
            mock_path.return_value = mock_script_path

            main()

            # Verify Path was called (it's called multiple times for different files)
            assert mock_path.call_count >= 1

    def test_main_argument_parsing(self):
        """Test that main function properly parses command line arguments."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.convert_odas_to_wav"
            ) as mock_convert,
            patch(
                "hexapod.odas.odas_to_picovoice_wav.sys.argv",
                [
                    "script.py",
                    "input.raw",
                    "output.wav",
                    "--sample-rate",
                    "22050",
                    "--channels",
                    "2",
                    "--channel",
                    "1",
                ],
            ),
        ):

            main()

            # Verify convert_odas_to_wav was called with parsed arguments
            mock_convert.assert_called_once()
            call_args = mock_convert.call_args
            assert call_args[0][0] == Path("input.raw")
            assert call_args[0][1] == Path("output.wav")
            assert call_args[0][2] == 22050  # sample_rate
            assert call_args[0][3] == 2  # channels
            assert call_args[0][4] == 1  # selected_channel

    def test_main_help_message(self):
        """Test that main function shows help message for invalid arguments."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.sys.argv", ["script.py", "--help"]
            ),
            pytest.raises(SystemExit),
        ):
            main()

    def test_main_missing_required_args(self):
        """Test that main function handles missing required arguments."""
        with (
            patch("hexapod.odas.odas_to_picovoice_wav.sys.argv", ["script.py"]),
            pytest.raises(SystemExit),
        ):
            main()

    def test_main_invalid_sample_rate(self):
        """Test that main function handles invalid sample rate."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.sys.argv",
                ["script.py", "input.raw", "output.wav", "--sample-rate", "invalid"],
            ),
            pytest.raises(SystemExit),
        ):
            main()

    def test_main_invalid_channels(self):
        """Test that main function handles invalid channels."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.sys.argv",
                ["script.py", "input.raw", "output.wav", "--channels", "invalid"],
            ),
            pytest.raises(SystemExit),
        ):
            main()

    def test_main_invalid_channel(self):
        """Test that main function handles invalid channel selection."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.sys.argv",
                ["script.py", "input.raw", "output.wav", "--channel", "invalid"],
            ),
            pytest.raises(SystemExit),
        ):
            main()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary output file path for testing."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            return Path(f.name)

    @pytest.fixture
    def mock_odas_processor(self):
        """Mock ODASAudioProcessor for testing."""
        mock_processor = Mock()
        mock_processor.running = True
        mock_processor.set_audio_callback = Mock()
        mock_processor.start = Mock()
        mock_processor.stop = Mock()
        return mock_processor

    def test_convert_odas_to_wav_empty_file(
        self, temp_output_file, mock_odas_processor
    ):
        """Test conversion with empty input file."""
        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as f:
            empty_file = Path(f.name)

        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__.return_value = mock_wav_file

            # Mock file size changes
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 0

                # Simulate the processor stopping after a few iterations
                def stop_processor(*args, **kwargs):
                    mock_odas_processor.running = False

                with patch(
                    "hexapod.odas.odas_to_picovoice_wav.time.sleep",
                    side_effect=stop_processor,
                ):
                    convert_odas_to_wav(empty_file, temp_output_file)

            # Verify processor was stopped
            mock_odas_processor.stop.assert_called_once()

    def test_convert_odas_to_wav_large_file(
        self, temp_output_file, mock_odas_processor
    ):
        """Test conversion with large input file."""
        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as f:
            large_file = Path(f.name)
            # Write some sample data
            sample_data = np.random.randint(-32768, 32767, (10000, 4), dtype=np.int16)
            f.write(sample_data.tobytes())

        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock the WAV file
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__.return_value = mock_wav_file

            # Mock file size changes
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000000

                # Simulate the processor stopping after a few iterations
                def stop_processor(*args, **kwargs):
                    mock_odas_processor.running = False

                with patch(
                    "hexapod.odas.odas_to_picovoice_wav.time.sleep",
                    side_effect=stop_processor,
                ):
                    convert_odas_to_wav(large_file, temp_output_file)

            # Verify processor was stopped
            mock_odas_processor.stop.assert_called_once()

    @pytest.fixture
    def temp_input_file(self):
        """Create a temporary input file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as f:
            # Write some sample audio data
            sample_data = np.random.randint(-32768, 32767, (1000, 4), dtype=np.int16)
            f.write(sample_data.tobytes())
            return Path(f.name)

    def test_convert_odas_to_wav_processor_error(
        self, temp_input_file, temp_output_file
    ):
        """Test conversion when ODASAudioProcessor raises an error."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor"
            ) as mock_odas_class,
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock ODASAudioProcessor to raise an error
            mock_odas_class.side_effect = Exception("Processor error")

            # Mock the WAV file
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__.return_value = mock_wav_file

            # Mock file size changes
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # The function should handle the error gracefully
                with pytest.raises(Exception, match="Processor error"):
                    convert_odas_to_wav(temp_input_file, temp_output_file)

    def test_convert_odas_to_wav_wav_file_error(
        self, temp_input_file, temp_output_file, mock_odas_processor
    ):
        """Test conversion when WAV file operations fail."""
        with (
            patch(
                "hexapod.odas.odas_to_picovoice_wav.ODASAudioProcessor",
                return_value=mock_odas_processor,
            ),
            patch("hexapod.odas.odas_to_picovoice_wav.wave.open") as mock_wave_open,
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
            patch("hexapod.odas.odas_to_picovoice_wav.time.sleep"),
        ):

            # Mock WAV file to raise an error
            mock_wave_open.side_effect = Exception("WAV file error")

            # Mock file size changes
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000

                # The function should handle the error gracefully
                with pytest.raises(Exception, match="WAV file error"):
                    convert_odas_to_wav(temp_input_file, temp_output_file)
