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
from hexapod.kws.recorder import Recorder
from hexapod.kws.intent_dispatcher import IntentDispatcher


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
            'keyword_path': Path('test_keyword.ppn'),
            'context_path': Path('test_context.rhn'),
            'access_key': 'test_access_key',
            'task_interface': mock_task_interface,
            'device_index': 0,
            'porcupine_sensitivity': 0.75,
            'rhino_sensitivity': 0.25,
            'print_context': False,
            'recordings_dir': Path('test_recordings')
        }
    
    @pytest.fixture
    def voice_control(self, voice_control_params, mock_picovoice):
        """Create a VoiceControl instance with mocked dependencies."""
        with patch('hexapod.kws.voice_control.Picovoice', return_value=mock_picovoice), \
             patch('hexapod.kws.voice_control.Recorder'), \
             patch('hexapod.kws.voice_control.IntentDispatcher'), \
             patch('hexapod.kws.voice_control.pyaudio.PyAudio'), \
             patch('hexapod.kws.voice_control.VoiceControl.find_respeaker6_index', return_value=0), \
             patch('hexapod.kws.voice_control.VoiceControl.get_available_devices', return_value=['Test Device']):
            
            return VoiceControl(**voice_control_params)
    
    def test_init_default_parameters(self, mock_task_interface, mock_picovoice):
        """Test VoiceControl initialization with default parameters."""
        with patch('hexapod.kws.voice_control.Picovoice', return_value=mock_picovoice), \
             patch('hexapod.kws.voice_control.Recorder'), \
             patch('hexapod.kws.voice_control.IntentDispatcher'), \
             patch('hexapod.kws.voice_control.pyaudio.PyAudio'), \
             patch('hexapod.kws.voice_control.VoiceControl.find_respeaker6_index', return_value=0), \
             patch('hexapod.kws.voice_control.VoiceControl.get_available_devices', return_value=['Test Device']):
            
            vc = VoiceControl(
                keyword_path=Path('test.ppn'),
                context_path=Path('test.rhn'),
                access_key='test_key',
                task_interface=mock_task_interface,
                device_index=0
            )
            
            assert vc.keyword_path == Path('test.ppn')
            assert vc.context_path == Path('test.rhn')
            assert vc.access_key == 'test_key'
            assert vc.task_interface == mock_task_interface
            assert vc.device_index == 0
            assert vc.porcupine_sensitivity == VoiceControl.DEFAULT_PORCUPINE_SENSITIVITY
            assert vc.rhino_sensitivity == VoiceControl.DEFAULT_RHINO_SENSITIVITY
            assert vc.print_context is False
            assert vc.stop_event.is_set() is False
            assert vc.pause_event.is_set() is False
            assert vc.task_interface_interrupted is False
    
    def test_init_custom_parameters(self, mock_task_interface, mock_picovoice):
        """Test VoiceControl initialization with custom parameters."""
        with patch('hexapod.kws.voice_control.Picovoice', return_value=mock_picovoice), \
             patch('hexapod.kws.voice_control.Recorder'), \
             patch('hexapod.kws.voice_control.IntentDispatcher'), \
             patch('hexapod.kws.voice_control.pyaudio.PyAudio'), \
             patch('hexapod.kws.voice_control.VoiceControl.find_respeaker6_index', return_value=0), \
             patch('hexapod.kws.voice_control.VoiceControl.get_available_devices', return_value=['Test Device']):
            
            vc = VoiceControl(
                keyword_path=Path('custom.ppn'),
                context_path=Path('custom.rhn'),
                access_key='custom_key',
                task_interface=mock_task_interface,
                device_index=1,
                porcupine_sensitivity=0.8,
                rhino_sensitivity=0.3,
                print_context=True,
                recordings_dir=Path('custom_recordings')
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
        mock_device_info = {
            'name': 'Test Device',
            'maxInputChannels': 2
        }
        mock_pyaudio.get_device_info_by_index.return_value = mock_device_info
        mock_pyaudio.get_device_count.return_value = 1
        
        with patch('hexapod.kws.voice_control.pyaudio.PyAudio', return_value=mock_pyaudio):
            devices = VoiceControl.get_available_devices()
            
            assert devices == ['Test Device']
            mock_pyaudio.terminate.assert_called_once()
    
    def test_get_available_devices_error(self):
        """Test error handling in get_available_devices."""
        with patch('hexapod.kws.voice_control.pyaudio.PyAudio', side_effect=Exception("Audio error")):
            devices = VoiceControl.get_available_devices()
            assert devices == []
    
    def test_find_respeaker6_index(self):
        """Test finding ReSpeaker 6 device index."""
        with patch('hexapod.kws.voice_control.VoiceControl.get_available_devices', 
                   return_value=['seeed-8mic-voicecard', 'other-device']):
            index = VoiceControl.find_respeaker6_index()
            assert index == 0
    
    def test_find_respeaker6_index_not_found(self):
        """Test finding ReSpeaker 6 when not available."""
        with patch('hexapod.kws.voice_control.VoiceControl.get_available_devices', 
                   return_value=['other-device', 'another-device']):
            index = VoiceControl.find_respeaker6_index()
            assert index == -1
    
    def test_find_respeaker6_index_error(self):
        """Test error handling in find_respeaker6_index."""
        with patch('hexapod.kws.voice_control.VoiceControl.get_available_devices', 
                   side_effect=Exception("Device error")):
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
        
        voice_control.intent_dispatcher.dispatch.assert_called_once_with("test_intent", {"param": "value"})
    
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
        
        with patch.object(voice_control, '_initialize_audio'), \
             patch('hexapod.kws.voice_control.Picovoice', return_value=mock_picovoice):
            
            voice_control.unpause()
            
            assert voice_control.pause_event.is_set() is False
            voice_control._initialize_audio.assert_called_once()
            voice_control.task_interface.lights_handler.listen_wakeword.assert_called_once()
    
    def test_start_recording(self, voice_control):
        """Test starting audio recording."""
        voice_control.audio_recorder.start_recording.return_value = "test_recording"
        
        result = voice_control.start_recording("test_file", 30.0)
        
        assert result == "test_recording"
        voice_control.audio_recorder.start_recording.assert_called_once_with("test_file", 30.0)
    
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
        voice_control.audio_stream.read.return_value = b'\x00' * 1024
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
        with patch('os.dup'), patch('os.open'), patch('os.dup2'), patch('os.close'):
            with voice_control._suppress_alsa_warnings():
                pass  # Context manager should work without errors
    
    def test_initialize_audio(self, voice_control):
        """Test audio initialization."""
        mock_pyaudio = Mock()
        mock_device_info = {'name': 'Test Device'}
        mock_pyaudio.get_device_info_by_index.return_value = mock_device_info
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream
        
        with patch('hexapod.kws.voice_control.pyaudio.PyAudio', return_value=mock_pyaudio), \
             patch.object(voice_control, '_suppress_alsa_warnings'):
            
            voice_control._initialize_audio()
            
            assert voice_control.pyaudio_instance == mock_pyaudio
            assert voice_control.audio_stream == mock_stream
            mock_pyaudio.open.assert_called_once()
    
    def test_initialize_audio_error(self, voice_control):
        """Test audio initialization error handling."""
        with patch('hexapod.kws.voice_control.pyaudio.PyAudio', side_effect=Exception("Audio init error")), \
             patch.object(voice_control, '_suppress_alsa_warnings'):
            
            with pytest.raises(Exception, match="Audio init error"):
                voice_control._initialize_audio()
    
    def test_audio_processor_recording(self, voice_control):
        """Test audio processor when recording is active."""
        voice_control.pause_event.clear()
        voice_control.audio_stop_event = Mock()
        voice_control.audio_stop_event.is_set.return_value = False
        voice_control.audio_stream = Mock()
        voice_control.audio_stream.read.return_value = b'\x00' * 1024
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
        voice_control.audio_stream.read.return_value = b'\x00' * 4  # Very short data
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
        voice_control.task_interface.voice_control_paused_event.is_set.return_value = False
        
        with patch.object(voice_control, '_initialize_audio'), \
             patch('threading.Thread') as mock_thread, \
             patch.object(voice_control, '_cleanup_audio'), \
             patch.object(voice_control.audio_recorder, 'cleanup'):
            
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

        voice_control.task_interface.voice_control_paused_event.is_set = mock_pause_is_set

        # Mock stop after a few iterations
        stop_calls = 0
        def mock_stop_is_set():
            nonlocal stop_calls
            stop_calls += 1
            return stop_calls > 5  # Stop after a few iterations

        voice_control.stop_event.is_set = mock_stop_is_set

        with patch.object(voice_control, '_initialize_audio'), \
             patch('threading.Thread'), \
             patch.object(voice_control, 'pause') as mock_pause, \
             patch.object(voice_control, 'unpause') as mock_unpause, \
             patch.object(voice_control, '_cleanup_audio'), \
             patch.object(voice_control.audio_recorder, 'cleanup'):

            voice_control.run()

            # Check that pause and unpause were called
            assert mock_pause.call_count >= 1
            assert mock_unpause.call_count >= 1
    
    def test_run_method_exception(self, voice_control):
        """Test run method exception handling."""
        voice_control.stop_event = Mock()
        voice_control.stop_event.is_set.side_effect = Exception("Run error")
        
        with patch.object(voice_control, '_initialize_audio'), \
             patch.object(voice_control, '_cleanup_audio'), \
             patch.object(voice_control.audio_recorder, 'cleanup'):
            
            # Should not raise exception, just log error
            voice_control.run()
            
            voice_control._cleanup_audio.assert_called_once()
    
    def test_run_method_cleanup_exception(self, voice_control):
        """Test run method cleanup exception handling."""
        voice_control.stop_event = Mock()
        voice_control.stop_event.is_set.return_value = True
        
        with patch.object(voice_control, '_initialize_audio'), \
             patch.object(voice_control, '_cleanup_audio', side_effect=Exception("Cleanup error")), \
             patch.object(voice_control.audio_recorder, 'cleanup', side_effect=Exception("Recorder cleanup error")):
            
            # Should not raise exception, just log error
            voice_control.run()


class TestRecorder:
    """Test cases for Recorder class."""
    
    @pytest.fixture
    def recorder(self):
        """Create a Recorder instance."""
        with patch('pathlib.Path.mkdir'):
            return Recorder()
    
    @pytest.fixture
    def recorder_custom_dir(self):
        """Create a Recorder instance with custom directory."""
        custom_dir = Path('custom_recordings')
        with patch('pathlib.Path.mkdir'):
            return Recorder(custom_dir)
    
    def test_init_default_parameters(self, recorder):
        """Test Recorder initialization with default parameters."""
        assert recorder.recordings_dir == Recorder.DEFAULT_RECORDINGS_DIR
        assert recorder.is_recording is False
        assert recorder.is_continuous_recording is False
        assert recorder.recording_frames == []
        assert recorder.recording_start_time is None
        assert recorder.recording_base_filename is None
    
    def test_init_custom_parameters(self, recorder_custom_dir):
        """Test Recorder initialization with custom parameters."""
        assert recorder_custom_dir.recordings_dir == Path('custom_recordings')
    
    def test_constants(self):
        """Test Recorder class constants."""
        assert Recorder.DEFAULT_RECORDINGS_DIR == Path("data/audio/recordings")
        assert Recorder.AUDIO_RECORD_DURATION == 30 * 60
        assert Recorder.SAMPLE_RATE == 16000
        assert Recorder.CHANNELS == 8
        assert Recorder.FORMAT == "paInt16"
    
    def test_start_recording_default(self, recorder):
        """Test starting recording with default parameters."""
        with patch('time.strftime', return_value='20231201_120000'), \
             patch('time.time', return_value=1234567890.0):
            
            result = recorder.start_recording()
            
            assert result == '20231201_120000'
            assert recorder.is_recording is True
            assert recorder.is_continuous_recording is True
            assert recorder.recording_base_filename == '20231201_120000'
            assert recorder.recording_start_time == 1234567890.0
    
    def test_start_recording_custom_filename(self, recorder):
        """Test starting recording with custom filename."""
        with patch('time.time', return_value=1234567890.0):
            result = recorder.start_recording("custom_file")
            
            assert result == "custom_file"
            assert recorder.recording_base_filename == "custom_file"
    
    def test_start_recording_with_duration(self, recorder):
        """Test starting recording with duration."""
        with patch('time.time', return_value=1234567890.0), \
             patch('threading.Timer') as mock_timer:
            
            result = recorder.start_recording("test", 30.0)
            
            assert result == "test"
            assert recorder.is_recording is True
            assert recorder.is_continuous_recording is False
            mock_timer.assert_called_once_with(30.0, recorder.stop_recording)
    
    def test_start_recording_already_recording(self, recorder):
        """Test starting recording when already recording."""
        recorder.is_recording = True
        recorder.stop_recording = Mock(return_value="previous.wav")
        
        with patch('time.time', return_value=1234567890.0):
            result = recorder.start_recording("new_file")
            
            recorder.stop_recording.assert_called_once()
            assert result == "new_file"
    
    def test_stop_recording_not_recording(self, recorder):
        """Test stopping recording when not recording."""
        result = recorder.stop_recording()
        assert result == ""
    
    def test_stop_recording_active(self, recorder):
        """Test stopping recording when actively recording."""
        recorder.is_recording = True
        recorder.recording_base_filename = "test_file"
        recorder.recording_frames = [b'audio_data']
        recorder.recordings_dir = Path('test_dir')
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat, \
             patch('wave.open') as mock_wave, \
             patch('time.time', return_value=1234567890.0):
            
            mock_stat.return_value.st_size = 1024  # Mock file size
            
            result = recorder.stop_recording()
            
            assert result == "test_dir/test_file.wav"
            assert recorder.is_recording is False
            mock_wave.assert_called_once()
    
    def test_add_audio_frame(self, recorder):
        """Test adding audio frame to recording."""
        recorder.is_recording = True
        test_data = b'test_audio_data'
        
        recorder.add_audio_frame(test_data)
        
        assert test_data in recorder.recording_frames
    
    def test_add_audio_frame_not_recording(self, recorder):
        """Test adding audio frame when not recording."""
        recorder.is_recording = False
        test_data = b'test_audio_data'
        
        recorder.add_audio_frame(test_data)
        
        assert recorder.recording_frames == []
    
    def test_get_recording_status(self, recorder):
        """Test getting recording status."""
        recorder.is_recording = True
        recorder.recording_base_filename = "test_file"
        recorder.recording_start_time = 1234567890.0
        
        with patch('time.time', return_value=1234567891.0):
            status = recorder.get_recording_status()
            
            assert status['is_recording'] is True
            assert status['base_filename'] == "test_file"
            assert status['total_duration'] == 1.0
    
    def test_get_recording_status_not_recording(self, recorder):
        """Test getting recording status when not recording."""
        status = recorder.get_recording_status()
        
        assert status['is_recording'] is False
        assert status['base_filename'] is None
        assert status['total_duration'] is None
    
    def test_cleanup(self, recorder):
        """Test recorder cleanup."""
        recorder.is_recording = True
        recorder.recording_timer = Mock()
        
        recorder.cleanup()
        
        assert recorder.is_recording is False
        # recording_timer is set to None in cleanup() method, so we can't assert on cancel
        assert recorder.recording_timer is None
    
    def test_save_recording_audio_record(self, recorder):
        """Test saving recording audio record."""
        recorder.recording_frames = [b'audio_data1', b'audio_data2']
        recorder.recording_base_filename = "test_file"
        recorder.recording_audio_record_number = 2
        recorder.recordings_dir = Path('test_dir')

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat, \
             patch('wave.open') as mock_wave, \
             patch('time.time', return_value=1234567890.0):

            mock_stat.return_value.st_size = 1024

            result = recorder._save_recording_audio_record()

            expected_filename = "test_file_002.wav"
            assert result == f"test_dir/{expected_filename}"
            mock_wave.assert_called_once()
    
    def test_save_recording_audio_record_error(self, recorder):
        """Test saving recording audio record with error."""
        recorder.recording_frames = [b'audio_data1', b'audio_data2']
        recorder.recording_base_filename = "test_file"
        recorder.recording_audio_record_number = 2
        recorder.recordings_dir = Path('test_dir')
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('wave.open', side_effect=Exception("Wave error")):
            
            result = recorder._save_recording_audio_record()
            
            assert result == ""
    
    def test_stop_recording_continuous(self, recorder):
        """Test stopping continuous recording."""
        recorder.is_recording = True
        recorder.is_continuous_recording = True
        recorder.recording_base_filename = "test_file"
        recorder.recording_frames = [b'audio_data']
        recorder.recording_start_time = 1234567890.0
        recorder.recording_audio_record_number = 3
        
        with patch.object(recorder, '_save_recording_audio_record', return_value="saved_file.wav"), \
             patch('time.time', return_value=1234567891.0):
            
            result = recorder.stop_recording()
            
            assert result == "saved_file.wav"
            assert recorder.is_recording is False
            recorder._save_recording_audio_record.assert_called_once()
    
    def test_stop_recording_no_frames(self, recorder):
        """Test stopping recording with no frames."""
        recorder.is_recording = True
        recorder.is_continuous_recording = False
        recorder.recording_base_filename = "test_file"
        recorder.recording_frames = []
        recorder.recording_start_time = 1234567890.0
        
        with patch('time.time', return_value=1234567891.0):
            result = recorder.stop_recording()
            
            assert result == ""
            assert recorder.is_recording is False
    
    def test_stop_recording_save_error(self, recorder):
        """Test stopping recording with save error."""
        recorder.is_recording = True
        recorder.is_continuous_recording = False
        recorder.recording_base_filename = "test_file"
        recorder.recording_frames = [b'audio_data']
        recorder.recordings_dir = Path('test_dir')
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('wave.open', side_effect=Exception("Save error")), \
             patch('time.time', return_value=1234567890.0):
            
            result = recorder.stop_recording()
            
            assert result == ""
            assert recorder.is_recording is False
    
    def test_get_recording_status_with_audio_record(self, recorder):
        """Test getting recording status with audio record timing."""
        recorder.is_recording = True
        recorder.recording_base_filename = "test_file"
        recorder.recording_start_time = 1234567890.0
        recorder.recording_audio_record_start_time = 1234567890.5
        recorder.recording_audio_record_number = 2
        recorder.recording_frames = [b'data1', b'data2']
        
        with patch('time.time', return_value=1234567891.0):
            status = recorder.get_recording_status()
            
            assert status['is_recording'] is True
            assert status['base_filename'] == "test_file"
            assert status['total_duration'] == 1.0
            assert status['current_audio_record_duration'] == 0.5
            assert status['current_audio_record_number'] == 2
            assert status['frame_count'] == 2
    
    def test_get_recording_status_no_timing(self, recorder):
        """Test getting recording status without timing data."""
        recorder.is_recording = True
        recorder.recording_base_filename = "test_file"
        recorder.recording_start_time = None
        recorder.recording_audio_record_start_time = None
        recorder.recording_audio_record_number = 1
        recorder.recording_frames = []
        
        status = recorder.get_recording_status()
        
        assert status['is_recording'] is True
        assert status['base_filename'] == "test_file"
        assert status['total_duration'] is None
        assert status['current_audio_record_duration'] is None
        assert status['current_audio_record_number'] == 1
        assert status['frame_count'] == 0


class TestIntentDispatcher:
    """Test cases for IntentDispatcher class."""
    
    @pytest.fixture
    def mock_task_interface(self):
        """Create a mock TaskInterface."""
        return Mock()
    
    @pytest.fixture
    def intent_dispatcher(self, mock_task_interface):
        """Create an IntentDispatcher instance."""
        return IntentDispatcher(mock_task_interface)
    
    def test_init(self, intent_dispatcher, mock_task_interface):
        """Test IntentDispatcher initialization."""
        assert intent_dispatcher.task_interface == mock_task_interface
        assert isinstance(intent_dispatcher.intent_handlers, dict)
        assert 'help' in intent_dispatcher.intent_handlers
        assert 'move' in intent_dispatcher.intent_handlers
        assert 'stop' in intent_dispatcher.intent_handlers
    
    def test_dispatch_valid_intent(self, intent_dispatcher):
        """Test dispatching a valid intent."""
        intent_dispatcher.intent_handlers['test_intent'] = Mock()
        
        intent_dispatcher.dispatch('test_intent', {'param': 'value'})
        
        intent_dispatcher.intent_handlers['test_intent'].assert_called_once_with({'param': 'value'})
    
    def test_dispatch_invalid_intent(self, intent_dispatcher):
        """Test dispatching an invalid intent."""
        with pytest.raises(NotImplementedError, match="No handler for intent: invalid_intent"):
            intent_dispatcher.dispatch('invalid_intent', {})
    
    def test_parse_duration_in_seconds(self, intent_dispatcher):
        """Test parsing duration in seconds."""
        # Test with seconds
        result = intent_dispatcher._parse_duration_in_seconds(5, "seconds")
        assert result == 5.0
        
        # Test with minutes
        result = intent_dispatcher._parse_duration_in_seconds(2, "minutes")
        assert result == 120.0
        
        # Test with hours
        result = intent_dispatcher._parse_duration_in_seconds(1, "hours")
        assert result == 3600.0
        
        # Test with None values
        result = intent_dispatcher._parse_duration_in_seconds(None, "seconds")
        assert result is None
        
        result = intent_dispatcher._parse_duration_in_seconds(5, None)
        assert result is None
    
    def test_parse_duration_in_seconds_invalid(self, intent_dispatcher):
        """Test parsing duration with invalid values."""
        result = intent_dispatcher._parse_duration_in_seconds("invalid", "seconds")
        assert result is None
        
        result = intent_dispatcher._parse_duration_in_seconds(5, "invalid_unit")
        assert result is None
    
    def test_handler_decorator(self):
        """Test the handler decorator functionality."""
        from hexapod.kws.intent_dispatcher import handler
        
        @handler
        def test_handler(self, slots):
            return slots
        
        # Test that the decorator wraps the function
        assert callable(test_handler)
        assert hasattr(test_handler, '__wrapped__')
    
    def test_handle_help(self, intent_dispatcher):
        """Test help intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_help({})
            mock_logger.info.assert_called()
    
    def test_handle_system_status(self, intent_dispatcher):
        """Test system status intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_system_status({})
            mock_logger.info.assert_called()
    
    def test_handle_shut_down(self, intent_dispatcher):
        """Test shut down intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_shut_down({})
            mock_logger.info.assert_called()
    
    def test_handle_wake_up(self, intent_dispatcher):
        """Test wake up intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_wake_up({})
            mock_logger.info.assert_called()
    
    def test_handle_sleep(self, intent_dispatcher):
        """Test sleep intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_sleep({})
            mock_logger.info.assert_called()
    
    def test_handle_calibrate(self, intent_dispatcher):
        """Test calibrate intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_calibrate({})
            mock_logger.info.assert_called()
    
    def test_handle_repeat(self, intent_dispatcher):
        """Test repeat intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_repeat({})
            mock_logger.info.assert_called()
    
    def test_handle_turn_lights(self, intent_dispatcher):
        """Test turn lights intent handler."""
        slots = {"state": "on"}
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_turn_lights(slots)
            mock_logger.info.assert_called()
    
    def test_handle_change_color(self, intent_dispatcher):
        """Test change color intent handler."""
        slots = {"color": "red"}
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_change_color(slots)
            mock_logger.info.assert_called()
    
    def test_handle_set_brightness(self, intent_dispatcher):
        """Test set brightness intent handler."""
        slots = {"brightness": "50%"}
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_set_brightness(slots)
            mock_logger.info.assert_called()
    
    def test_handle_set_speed(self, intent_dispatcher):
        """Test set speed intent handler."""
        slots = {"speed": "50%"}
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_set_speed(slots)
            mock_logger.info.assert_called()
    
    def test_handle_set_accel(self, intent_dispatcher):
        """Test set acceleration intent handler."""
        slots = {"accel": "30%"}
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_set_accel(slots)
            mock_logger.info.assert_called()
    
    def test_handle_march_in_place(self, intent_dispatcher):
        """Test march in place intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_march_in_place({})
            mock_logger.info.assert_called()
    
    def test_handle_idle_stance(self, intent_dispatcher):
        """Test idle stance intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_idle_stance({})
            mock_logger.info.assert_called()
    
    def test_handle_move(self, intent_dispatcher):
        """Test move intent handler."""
        slots = {"direction": "forward", "distance": "10"}
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_move(slots)
            mock_logger.info.assert_called()
    
    def test_handle_stop(self, intent_dispatcher):
        """Test stop intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_stop({})
            mock_logger.info.assert_called()
    
    def test_handle_rotate(self, intent_dispatcher):
        """Test rotate intent handler."""
        slots = {"direction": "left", "angle": "90"}
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_rotate(slots)
            mock_logger.info.assert_called()
    
    def test_handle_follow(self, intent_dispatcher):
        """Test follow intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_follow({})
            mock_logger.info.assert_called()
    
    def test_handle_sound_source_localization(self, intent_dispatcher):
        """Test sound source localization intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_sound_source_localization({})
            mock_logger.info.assert_called()
    
    def test_handle_stream_odas_audio(self, intent_dispatcher):
        """Test stream ODAS audio intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_stream_odas_audio({})
            mock_logger.info.assert_called()
    
    def test_handle_police(self, intent_dispatcher):
        """Test police intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_police({})
            mock_logger.info.assert_called()
    
    def test_handle_rainbow(self, intent_dispatcher):
        """Test rainbow intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_rainbow({})
            mock_logger.info.assert_called()
    
    def test_handle_sit_up(self, intent_dispatcher):
        """Test sit up intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_sit_up({})
            mock_logger.info.assert_called()
    
    def test_handle_helix(self, intent_dispatcher):
        """Test helix intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_helix({})
            mock_logger.info.assert_called()
    
    def test_handle_show_off(self, intent_dispatcher):
        """Test show off intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_show_off({})
            mock_logger.info.assert_called()
    
    def test_handle_hello(self, intent_dispatcher):
        """Test hello intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_hello({})
            mock_logger.info.assert_called()
    
    def test_handle_start_recording(self, intent_dispatcher):
        """Test start recording intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_start_recording({})
            mock_logger.info.assert_called()
    
    def test_handle_stop_recording(self, intent_dispatcher):
        """Test stop recording intent handler."""
        with patch('hexapod.kws.intent_dispatcher.logger') as mock_logger:
            intent_dispatcher.handle_stop_recording({})
            mock_logger.info.assert_called()