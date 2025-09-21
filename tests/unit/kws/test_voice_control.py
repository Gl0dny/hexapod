"""
Unit tests for voice control system.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import numpy as np

from hexapod.kws.voice_control import VoiceControl


class TestVoiceControl:
    """Test cases for VoiceControl class."""

    @pytest.fixture
    def mock_task_interface(self):
        """Create a mock TaskInterface."""
        task_interface = Mock()
        task_interface.lights_handler = Mock()
        task_interface.voice_control_paused_event = threading.Event()
        task_interface.voice_control_context_info = None
        task_interface.task = None
        task_interface.stop = Mock()
        task_interface.set_task_complete_callback = Mock()
        return task_interface

    @pytest.fixture
    def mock_picovoice(self):
        """Create a mock Picovoice instance."""
        picovoice = Mock()
        picovoice.frame_length = 512
        picovoice.context_info = "Test context info"
        picovoice.process = Mock()
        picovoice.delete = Mock()
        return picovoice

    @pytest.fixture
    def voice_control_params(self, mock_task_interface):
        """Create standard VoiceControl parameters."""
        return {
            "keyword_path": Path("test_keyword.ppn"),
            "context_path": Path("test_context.rhn"),
            "access_key": "test_access_key",
            "task_interface": mock_task_interface,
            "device_index": 0,
            "porcupine_sensitivity": 0.75,
            "rhino_sensitivity": 0.25,
            "print_context": False,
            "recordings_dir": Path("test_recordings"),
        }

    @pytest.fixture
    def voice_control(self, voice_control_params, mock_picovoice):
        """Create a VoiceControl instance with mocked dependencies."""
        with (
            patch("hexapod.kws.voice_control.Picovoice", return_value=mock_picovoice),
            patch("hexapod.kws.voice_control.Recorder"),
            patch("hexapod.kws.voice_control.IntentDispatcher"),
            patch("hexapod.kws.voice_control.pyaudio.PyAudio"),
            patch(
                "hexapod.kws.voice_control.VoiceControl.find_respeaker6_index",
                return_value=0,
            ),
            patch(
                "hexapod.kws.voice_control.VoiceControl.get_available_devices",
                return_value=["Test Device"],
            ),
        ):

            return VoiceControl(**voice_control_params)

    def test_init_default_parameters(self, mock_task_interface, mock_picovoice):
        """Test VoiceControl initialization with default parameters."""
        with (
            patch("hexapod.kws.voice_control.Picovoice", return_value=mock_picovoice),
            patch("hexapod.kws.voice_control.Recorder"),
            patch("hexapod.kws.voice_control.IntentDispatcher"),
            patch("hexapod.kws.voice_control.pyaudio.PyAudio"),
            patch(
                "hexapod.kws.voice_control.VoiceControl.find_respeaker6_index",
                return_value=0,
            ),
            patch(
                "hexapod.kws.voice_control.VoiceControl.get_available_devices",
                return_value=["Test Device"],
            ),
        ):

            vc = VoiceControl(
                keyword_path=Path("test.ppn"),
                context_path=Path("test.rhn"),
                access_key="test_key",
                task_interface=mock_task_interface,
                device_index=0,
            )

            assert vc.keyword_path == Path("test.ppn")
            assert vc.context_path == Path("test.rhn")
            assert vc.access_key == "test_key"
            assert vc.task_interface == mock_task_interface
            assert vc.device_index == 0
            assert (
                vc.porcupine_sensitivity == VoiceControl.DEFAULT_PORCUPINE_SENSITIVITY
            )
            assert vc.rhino_sensitivity == VoiceControl.DEFAULT_RHINO_SENSITIVITY
            assert vc.print_context is False
            assert vc.stop_event.is_set() is False
            assert vc.pause_event.is_set() is False
            assert vc.task_interface_interrupted is False

    def test_init_custom_parameters(self, mock_task_interface, mock_picovoice):
        """Test VoiceControl initialization with custom parameters."""
        with (
            patch("hexapod.kws.voice_control.Picovoice", return_value=mock_picovoice),
            patch("hexapod.kws.voice_control.Recorder"),
            patch("hexapod.kws.voice_control.IntentDispatcher"),
            patch("hexapod.kws.voice_control.pyaudio.PyAudio"),
            patch(
                "hexapod.kws.voice_control.VoiceControl.find_respeaker6_index",
                return_value=0,
            ),
            patch(
                "hexapod.kws.voice_control.VoiceControl.get_available_devices",
                return_value=["Test Device"],
            ),
        ):

            vc = VoiceControl(
                keyword_path=Path("custom.ppn"),
                context_path=Path("custom.rhn"),
                access_key="custom_key",
                task_interface=mock_task_interface,
                device_index=1,
                porcupine_sensitivity=0.8,
                rhino_sensitivity=0.3,
                print_context=True,
                recordings_dir=Path("custom_recordings"),
            )

            assert vc.porcupine_sensitivity == 0.8
            assert vc.rhino_sensitivity == 0.3
            assert vc.print_context is True
            # recordings_dir is passed to Recorder, not stored directly on VoiceControl

    def test_constants(self):
        """Test VoiceControl class constants."""
        assert VoiceControl.DEFAULT_PORCUPINE_SENSITIVITY == 0.75
        assert VoiceControl.DEFAULT_RHINO_SENSITIVITY == 0.25
        assert VoiceControl.SAMPLE_RATE == 16000
        assert VoiceControl.CHANNELS == 8
        assert VoiceControl.CHUNK_SIZE == 512
        assert VoiceControl.FORMAT == "paInt16"

    def test_get_available_devices(self):
        """Test getting available audio devices."""
        mock_pyaudio = Mock()
        mock_device_info = {"name": "Test Device", "maxInputChannels": 2}
        mock_pyaudio.get_device_info_by_index.return_value = mock_device_info
        mock_pyaudio.get_device_count.return_value = 1

        with patch(
            "hexapod.kws.voice_control.pyaudio.PyAudio", return_value=mock_pyaudio
        ):
            devices = VoiceControl.get_available_devices()

            assert devices == ["Test Device"]
            mock_pyaudio.terminate.assert_called_once()

    def test_get_available_devices_error(self):
        """Test error handling in get_available_devices."""
        with patch(
            "hexapod.kws.voice_control.pyaudio.PyAudio",
            side_effect=Exception("Audio error"),
        ):
            devices = VoiceControl.get_available_devices()
            assert devices == []

    def test_find_respeaker6_index(self):
        """Test finding ReSpeaker 6 device index."""
        with patch(
            "hexapod.kws.voice_control.VoiceControl.get_available_devices",
            return_value=["seeed-8mic-voicecard", "other-device"],
        ):
            index = VoiceControl.find_respeaker6_index()
            assert index == 0

    def test_find_respeaker6_index_not_found(self):
        """Test finding ReSpeaker 6 when not available."""
        with patch(
            "hexapod.kws.voice_control.VoiceControl.get_available_devices",
            return_value=["other-device", "another-device"],
        ):
            index = VoiceControl.find_respeaker6_index()
            assert index == -1

    def test_find_respeaker6_index_error(self):
        """Test error handling in find_respeaker6_index."""
        with patch(
            "hexapod.kws.voice_control.VoiceControl.get_available_devices",
            side_effect=Exception("Device error"),
        ):
            index = VoiceControl.find_respeaker6_index()
            assert index == -1

    def test_wake_word_callback(self, voice_control):
        """Test wake word callback functionality."""
        voice_control.task_interface.task = Mock()
        voice_control.task_interface.task.__class__.__name__ = "TestTask"

        voice_control._wake_word_callback()

        voice_control.task_interface.lights_handler.listen_intent.assert_called_once()
        voice_control.task_interface.stop.assert_called_once()
        assert voice_control.task_interface_interrupted is True

    def test_wake_word_callback_no_task(self, voice_control):
        """Test wake word callback when no task is running."""
        voice_control.task_interface.task = None

        voice_control._wake_word_callback()

        voice_control.task_interface.lights_handler.listen_intent.assert_called_once()
        voice_control.task_interface.stop.assert_not_called()
        assert voice_control.task_interface_interrupted is False

    def test_inference_callback_understood(self, voice_control):
        """Test inference callback when intent is understood."""
        mock_inference = Mock()
        mock_inference.is_understood = True
        mock_inference.intent = "test_intent"
        mock_inference.slots = {"param": "value"}

        voice_control._inference_callback(mock_inference)

        voice_control.intent_dispatcher.dispatch.assert_called_once_with(
            "test_intent", {"param": "value"}
        )

    def test_inference_callback_not_understood(self, voice_control):
        """Test inference callback when intent is not understood."""
        mock_inference = Mock()
        mock_inference.is_understood = False
        mock_inference.intent = None
        mock_inference.slots = None

        voice_control._inference_callback(mock_inference)

        voice_control.intent_dispatcher.dispatch.assert_not_called()
        voice_control.task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_inference_callback_not_understood_paused(self, voice_control):
        """Test inference callback when not understood and voice control is paused."""
        mock_inference = Mock()
        mock_inference.is_understood = False
        voice_control.task_interface.voice_control_paused_event.set()

        voice_control._inference_callback(mock_inference)

        voice_control.task_interface.lights_handler.listen_wakeword.assert_not_called()

    def test_on_task_complete(self, voice_control):
        """Test task completion callback."""
        mock_task = Mock()
        mock_task.__class__.__name__ = "TestTask"

        voice_control.on_task_complete(mock_task)

        voice_control.task_interface.lights_handler.listen_wakeword.assert_called_once()
        assert voice_control.task_interface_interrupted is False

    def test_on_task_complete_stopped(self, voice_control):
        """Test task completion callback when voice control is stopped."""
        mock_task = Mock()
        voice_control.stop_event.set()

        voice_control.on_task_complete(mock_task)

        voice_control.task_interface.lights_handler.listen_wakeword.assert_not_called()

    def test_on_task_complete_interrupted(self, voice_control):
        """Test task completion callback when task was interrupted."""
        mock_task = Mock()
        voice_control.task_interface_interrupted = True

        voice_control.on_task_complete(mock_task)

        voice_control.task_interface.lights_handler.listen_wakeword.assert_not_called()
        assert voice_control.task_interface_interrupted is False

    def test_pause(self, voice_control):
        """Test pausing voice control."""
        voice_control.audio_thread = Mock()
        voice_control.audio_thread.is_alive.return_value = True
        voice_control.audio_stream = Mock()
        voice_control.pyaudio_instance = Mock()
        voice_control.picovoice = Mock()
        voice_control.audio_stop_event = Mock()

        voice_control.pause()

        assert voice_control.pause_event.is_set() is True
        voice_control.audio_stop_event.set.assert_called_once()
        # audio_thread, audio_stream, and picovoice are set to None in pause() method, so we can't assert on their methods
        voice_control.task_interface.lights_handler.off.assert_called_once()

    def test_unpause(self, voice_control, mock_picovoice):
        """Test unpausing voice control."""
        voice_control.pause_event.set()
        voice_control.picovoice = None

        with (
            patch.object(voice_control, "_initialize_audio"),
            patch("hexapod.kws.voice_control.Picovoice", return_value=mock_picovoice),
        ):

            voice_control.unpause()

            assert voice_control.pause_event.is_set() is False
            voice_control._initialize_audio.assert_called_once()
            voice_control.task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_start_recording(self, voice_control):
        """Test starting audio recording."""
        voice_control.audio_recorder.start_recording.return_value = "test_recording"

        result = voice_control.start_recording("test_file", 30.0)

        assert result == "test_recording"
        voice_control.audio_recorder.start_recording.assert_called_once_with(
            "test_file", 30.0
        )

    def test_stop_recording(self, voice_control):
        """Test stopping audio recording."""
        voice_control.audio_recorder.stop_recording.return_value = "test_recording.wav"

        result = voice_control.stop_recording()

        assert result == "test_recording.wav"
        voice_control.audio_recorder.stop_recording.assert_called_once()

    def test_get_recording_status(self, voice_control):
        """Test getting recording status."""
        expected_status = {"is_recording": True, "filename": "test.wav"}
        voice_control.audio_recorder.get_recording_status.return_value = expected_status

        result = voice_control.get_recording_status()

        assert result == expected_status
        voice_control.audio_recorder.get_recording_status.assert_called_once()

    def test_stop(self, voice_control):
        """Test stopping voice control thread."""
        voice_control.stop()

        assert voice_control.stop_event.is_set() is True

    def test_print_context_info(self, voice_control, capsys):
        """Test printing context information."""
        voice_control.context = "Test context information"

        voice_control.print_context_info()

        captured = capsys.readouterr()
        assert "Test context information" in captured.out

    def test_audio_processor_paused(self, voice_control):
        """Test audio processor when paused."""
        voice_control.pause_event.set()
        voice_control.audio_stop_event = Mock()
        voice_control.audio_stop_event.is_set.return_value = False

        # Mock the while loop to run once
        original_is_set = voice_control.audio_stop_event.is_set
        call_count = 0

        def mock_is_set():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return False
            return True

        voice_control.audio_stop_event.is_set = mock_is_set

        voice_control._audio_processor()

        # Should sleep when paused
        assert call_count > 0

    def test_audio_processor_processing(self, voice_control):
        """Test audio processor when processing audio."""
        voice_control.pause_event.clear()
        voice_control.audio_stop_event = Mock()
        voice_control.audio_stop_event.is_set.return_value = False
        voice_control.audio_stream = Mock()
        voice_control.audio_stream.read.return_value = b"\x00" * 1024
        voice_control.picovoice = Mock()
        voice_control.audio_recorder = Mock()
        voice_control.audio_recorder.is_recording = False

        # Mock the while loop to run once
        original_is_set = voice_control.audio_stop_event.is_set
        call_count = 0

        def mock_is_set():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return False
            return True

        voice_control.audio_stop_event.is_set = mock_is_set

        voice_control._audio_processor()

        voice_control.audio_stream.read.assert_called_once()
        voice_control.picovoice.process.assert_called_once()

    def test_cleanup_audio(self, voice_control):
        """Test audio cleanup."""
        voice_control.audio_thread = Mock()
        voice_control.audio_thread.is_alive.return_value = True
        voice_control.audio_stream = Mock()
        voice_control.pyaudio_instance = Mock()
        voice_control.audio_stop_event = Mock()

        voice_control._cleanup_audio()

        voice_control.audio_stop_event.set.assert_called_once()
        # audio_thread and audio_stream are set to None in _cleanup_audio() method, so we can't assert on their methods

    def test_cleanup_audio_error(self, voice_control):
        """Test audio cleanup with errors."""
        voice_control.audio_thread = Mock()
        voice_control.audio_thread.is_alive.return_value = True
        voice_control.audio_thread.join.side_effect = Exception("Join error")
        voice_control.audio_stream = Mock()
        voice_control.audio_stream.stop_stream.side_effect = Exception("Stream error")

        # Should not raise exception
        voice_control._cleanup_audio()

    def test_suppress_alsa_warnings(self, voice_control):
        """Test ALSA warnings suppression context manager."""
        with patch("os.dup"), patch("os.open"), patch("os.dup2"), patch("os.close"):
            with voice_control._suppress_alsa_warnings():
                pass  # Context manager should work without errors

    def test_initialize_audio(self, voice_control):
        """Test audio initialization."""
        mock_pyaudio = Mock()
        mock_device_info = {"name": "Test Device"}
        mock_pyaudio.get_device_info_by_index.return_value = mock_device_info
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream

        with (
            patch(
                "hexapod.kws.voice_control.pyaudio.PyAudio", return_value=mock_pyaudio
            ),
            patch.object(voice_control, "_suppress_alsa_warnings"),
        ):

            voice_control._initialize_audio()

            assert voice_control.pyaudio_instance == mock_pyaudio
            assert voice_control.audio_stream == mock_stream
            mock_pyaudio.open.assert_called_once()

    def test_initialize_audio_error(self, voice_control):
        """Test audio initialization error handling."""
        with (
            patch(
                "hexapod.kws.voice_control.pyaudio.PyAudio",
                side_effect=Exception("Audio init error"),
            ),
            patch.object(voice_control, "_suppress_alsa_warnings"),
        ):

            with pytest.raises(Exception, match="Audio init error"):
                voice_control._initialize_audio()

    def test_audio_processor_recording(self, voice_control):
        """Test audio processor when recording is active."""
        voice_control.pause_event.clear()
        voice_control.audio_stop_event = Mock()
        voice_control.audio_stop_event.is_set.return_value = False
        voice_control.audio_stream = Mock()
        voice_control.audio_stream.read.return_value = b"\x00" * 1024
        voice_control.picovoice = Mock()
        voice_control.audio_recorder = Mock()
        voice_control.audio_recorder.is_recording = True
        voice_control.audio_recorder.add_audio_frame = Mock()

        # Mock the while loop to run once
        call_count = 0

        def mock_is_set():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return False
            return True

        voice_control.audio_stop_event.is_set = mock_is_set

        voice_control._audio_processor()

        voice_control.audio_stream.read.assert_called_once()
        voice_control.picovoice.process.assert_called_once()
        voice_control.audio_recorder.add_audio_frame.assert_called_once()

    def test_audio_processor_short_data(self, voice_control):
        """Test audio processor with short audio data."""
        voice_control.pause_event.clear()
        voice_control.audio_stop_event = Mock()
        voice_control.audio_stop_event.is_set.return_value = False
        voice_control.audio_stream = Mock()
        voice_control.audio_stream.read.return_value = b"\x00" * 4  # Very short data
        voice_control.picovoice = Mock()
        voice_control.picovoice.frame_length = 512
        voice_control.audio_recorder = Mock()
        voice_control.audio_recorder.is_recording = False

        # Mock the while loop to run once
        call_count = 0

        def mock_is_set():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return False
            return True

        voice_control.audio_stop_event.is_set = mock_is_set

        voice_control._audio_processor()

        voice_control.audio_stream.read.assert_called_once()
        voice_control.picovoice.process.assert_called_once()

    def test_audio_processor_error(self, voice_control):
        """Test audio processor error handling."""
        voice_control.pause_event.clear()
        voice_control.audio_stop_event = Mock()
        voice_control.audio_stop_event.is_set.return_value = False
        voice_control.audio_stream = Mock()
        voice_control.audio_stream.read.side_effect = Exception("Audio read error")
        voice_control.picovoice = Mock()
        voice_control.audio_recorder = Mock()
        voice_control.audio_recorder.is_recording = False

        # Mock the while loop to run once
        call_count = 0

        def mock_is_set():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return False
            return True

        voice_control.audio_stop_event.is_set = mock_is_set

        # Should not raise exception, just log error
        voice_control._audio_processor()

        voice_control.audio_stream.read.assert_called_once()

    def test_audio_processor_thread_error(self, voice_control):
        """Test audio processor thread error handling."""
        voice_control.pause_event.clear()
        voice_control.audio_stop_event = Mock()
        voice_control.audio_stop_event.is_set.side_effect = Exception("Thread error")

        # Should not raise exception, just log error
        voice_control._audio_processor()

    def test_run_method(self, voice_control):
        """Test the main run method."""
        voice_control.stop_event = Mock()
        voice_control.stop_event.is_set.return_value = True  # Stop immediately
        voice_control.task_interface.voice_control_paused_event = Mock()
        voice_control.task_interface.voice_control_paused_event.is_set.return_value = (
            False
        )

        with (
            patch.object(voice_control, "_initialize_audio"),
            patch("threading.Thread") as mock_thread,
            patch.object(voice_control, "_cleanup_audio"),
            patch.object(voice_control.audio_recorder, "cleanup"),
        ):

            voice_control.run()

            voice_control._initialize_audio.assert_called_once()
            voice_control._cleanup_audio.assert_called_once()
            voice_control.audio_recorder.cleanup.assert_called_once()

    def test_run_method_pause_unpause(self, voice_control):
        """Test run method with pause/unpause logic."""
        voice_control.stop_event = Mock()
        voice_control.stop_event.is_set.return_value = False
        voice_control.task_interface.voice_control_paused_event = Mock()

        # Simulate pause state change - start not paused, then pause, then unpause
        pause_state = [False, True, False]  # Start normal, then pause, then unpause
        pause_call_count = 0

        def mock_pause_is_set():
            nonlocal pause_call_count
            if pause_call_count < len(pause_state):
                result = pause_state[pause_call_count]
                pause_call_count += 1
                return result
            return False

        voice_control.task_interface.voice_control_paused_event.is_set = (
            mock_pause_is_set
        )

        # Mock stop after a few iterations
        stop_calls = 0

        def mock_stop_is_set():
            nonlocal stop_calls
            stop_calls += 1
            return stop_calls > 5  # Stop after a few iterations

        voice_control.stop_event.is_set = mock_stop_is_set

        with (
            patch.object(voice_control, "_initialize_audio"),
            patch("threading.Thread"),
            patch.object(voice_control, "pause") as mock_pause,
            patch.object(voice_control, "unpause") as mock_unpause,
            patch.object(voice_control, "_cleanup_audio"),
            patch.object(voice_control.audio_recorder, "cleanup"),
        ):

            voice_control.run()

            # Check that pause and unpause were called
            assert mock_pause.call_count >= 1
            assert mock_unpause.call_count >= 1

    def test_run_method_exception(self, voice_control):
        """Test run method exception handling."""
        voice_control.stop_event = Mock()
        voice_control.stop_event.is_set.side_effect = Exception("Run error")

        with (
            patch.object(voice_control, "_initialize_audio"),
            patch.object(voice_control, "_cleanup_audio"),
            patch.object(voice_control.audio_recorder, "cleanup"),
        ):

            # Should not raise exception, just log error
            voice_control.run()

            voice_control._cleanup_audio.assert_called_once()

    def test_run_method_cleanup_exception(self, voice_control):
        """Test run method cleanup exception handling."""
        voice_control.stop_event = Mock()
        voice_control.stop_event.is_set.return_value = True

        with (
            patch.object(voice_control, "_initialize_audio"),
            patch.object(
                voice_control, "_cleanup_audio", side_effect=Exception("Cleanup error")
            ),
            patch.object(
                voice_control.audio_recorder,
                "cleanup",
                side_effect=Exception("Recorder cleanup error"),
            ),
        ):

            # Should not raise exception, just log error
            voice_control.run()
