"""
Unit tests for audio recorder system.
"""
import pytest
import time
import threading
import wave
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from hexapod.kws.recorder import Recorder


class TestRecorder:
    """Test cases for Recorder class."""
    
    @pytest.fixture
    def temp_recordings_dir(self, tmp_path):
        """Create a temporary recordings directory."""
        return tmp_path / "recordings"
    
    @pytest.fixture
    def recorder_default(self, temp_recordings_dir):
        """Create a Recorder instance with default parameters."""
        return Recorder()
    
    @pytest.fixture
    def recorder_custom(self, temp_recordings_dir):
        """Create a Recorder instance with custom parameters."""
        return Recorder(recordings_dir=temp_recordings_dir)
    
    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data."""
        return b"sample_audio_data_16bit"
    
    def test_init_default_parameters(self, recorder_default):
        """Test Recorder initialization with default parameters."""
        assert recorder_default.recordings_dir == Path("data/audio/recordings")
        assert recorder_default.is_recording is False
        assert recorder_default.is_continuous_recording is False
        assert recorder_default.recording_frames == []
        assert recorder_default.recording_start_time is None
        assert recorder_default.recording_audio_record_start_time is None
        assert recorder_default.recording_audio_record_number == 1
        assert recorder_default.recording_base_filename is None
        assert recorder_default.recording_timer is None
    
    def test_init_custom_parameters(self, temp_recordings_dir, recorder_custom):
        """Test Recorder initialization with custom parameters."""
        assert recorder_custom.recordings_dir == temp_recordings_dir
        assert recorder_custom.is_recording is False
        assert recorder_custom.is_continuous_recording is False
        assert recorder_custom.recording_frames == []
        assert recorder_custom.recording_start_time is None
        assert recorder_custom.recording_audio_record_start_time is None
        assert recorder_custom.recording_audio_record_number == 1
        assert recorder_custom.recording_base_filename is None
        assert recorder_custom.recording_timer is None
    
    def test_constants(self):
        """Test class constants."""
        assert Recorder.DEFAULT_RECORDINGS_DIR == Path("data/audio/recordings")
        assert Recorder.AUDIO_RECORD_DURATION == 30 * 60  # 30 minutes
        assert Recorder.SAMPLE_RATE == 16000
        assert Recorder.CHANNELS == 8
        assert Recorder.FORMAT == "paInt16"
    
    @patch('time.time')
    @patch('time.strftime')
    def test_start_recording_with_custom_filename(self, mock_strftime, mock_time, recorder_custom):
        """Test starting recording with custom filename."""
        mock_time.return_value = 1000.0
        mock_strftime.return_value = "20231201_120000"
        
        filename = "test_recording"
        result = recorder_custom.start_recording(filename=filename)
        
        assert result == filename
        assert recorder_custom.recording_base_filename == filename
        assert recorder_custom.is_recording is True
        assert recorder_custom.is_continuous_recording is True
        assert recorder_custom.recording_start_time == 1000.0
        assert recorder_custom.recording_audio_record_start_time == 1000.0
        assert recorder_custom.recording_audio_record_number == 1
        assert recorder_custom.recording_frames == []
        assert recorder_custom.recording_timer is None
    
    @patch('time.time')
    @patch('time.strftime')
    def test_start_recording_with_timestamp_filename(self, mock_strftime, mock_time, recorder_custom):
        """Test starting recording with timestamp filename."""
        mock_time.return_value = 1000.0
        mock_strftime.return_value = "20231201_120000"
        
        result = recorder_custom.start_recording()
        
        assert result == "20231201_120000"
        assert recorder_custom.recording_base_filename == "20231201_120000"
        assert recorder_custom.is_recording is True
        assert recorder_custom.is_continuous_recording is True
        assert recorder_custom.recording_start_time == 1000.0
        assert recorder_custom.recording_audio_record_start_time == 1000.0
        assert recorder_custom.recording_audio_record_number == 1
        assert recorder_custom.recording_frames == []
        assert recorder_custom.recording_timer is None
    
    @patch('time.time')
    @patch('time.strftime')
    def test_start_recording_with_duration(self, mock_strftime, mock_time, recorder_custom):
        """Test starting recording with duration."""
        mock_time.return_value = 1000.0
        mock_strftime.return_value = "20231201_120000"
        
        with patch('threading.Timer') as mock_timer:
            result = recorder_custom.start_recording(duration=60.0)
            
            assert result == "20231201_120000"  # From strftime mock
            assert recorder_custom.is_recording is True
            assert recorder_custom.is_continuous_recording is False
            assert recorder_custom.recording_timer is not None
            mock_timer.assert_called_once_with(60.0, recorder_custom.stop_recording)
    
    @patch('time.time')
    def test_start_recording_already_recording(self, mock_time, recorder_custom):
        """Test starting recording when already recording."""
        mock_time.return_value = 1000.0
        
        # Start first recording
        recorder_custom.start_recording("first_recording")
        
        # Mock stop_recording to avoid file operations
        with patch.object(recorder_custom, 'stop_recording') as mock_stop:
            # Start second recording
            result = recorder_custom.start_recording("second_recording")
            
            assert result == "second_recording"
            assert recorder_custom.recording_base_filename == "second_recording"
            mock_stop.assert_called_once()
    
    def test_add_audio_frame_not_recording(self, recorder_custom, sample_audio_data):
        """Test adding audio frame when not recording."""
        recorder_custom.add_audio_frame(sample_audio_data)
        assert recorder_custom.recording_frames == []
    
    def test_add_audio_frame_recording(self, recorder_custom, sample_audio_data):
        """Test adding audio frame when recording."""
        recorder_custom.is_recording = True
        recorder_custom.recording_frames = []
        
        recorder_custom.add_audio_frame(sample_audio_data)
        
        assert recorder_custom.recording_frames == [sample_audio_data]
    
    
    def test_save_recording_audio_record_no_frames(self, recorder_custom):
        """Test saving audio record with no frames."""
        recorder_custom.recording_frames = []
        
        result = recorder_custom._save_recording_audio_record()
        
        assert result == ""
    
    @patch('time.time')
    @patch('wave.open')
    @patch('pathlib.Path.stat')
    def test_save_recording_audio_record_success(self, mock_stat, mock_wave_open, mock_time, recorder_custom, sample_audio_data):
        """Test successful saving of audio record."""
        mock_time.return_value = 2000.0
        mock_stat.return_value.st_size = 1024 * 1024  # 1MB
        
        recorder_custom.recording_frames = [sample_audio_data]
        recorder_custom.recording_base_filename = "test_recording"
        recorder_custom.recording_audio_record_number = 1
        recorder_custom.recording_audio_record_start_time = 1000.0
        
        mock_wf = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wf
        
        result = recorder_custom._save_recording_audio_record()
        
        assert result == str(recorder_custom.recordings_dir / "test_recording_001.wav")
        assert recorder_custom.recording_frames == []
        assert recorder_custom.recording_audio_record_start_time == 2000.0
        assert recorder_custom.recording_audio_record_number == 2
        
        # Verify wave file setup
        mock_wf.setnchannels.assert_called_once_with(8)
        mock_wf.setsampwidth.assert_called_once_with(2)
        mock_wf.setframerate.assert_called_once_with(16000)
        mock_wf.writeframes.assert_called_once_with(sample_audio_data)
    
    @patch('time.time')
    @patch('wave.open')
    def test_save_recording_audio_record_exception(self, mock_wave_open, mock_time, recorder_custom, sample_audio_data):
        """Test saving audio record with exception."""
        mock_time.return_value = 2000.0
        mock_wave_open.side_effect = Exception("File write error")
        
        recorder_custom.recording_frames = [sample_audio_data]
        recorder_custom.recording_base_filename = "test_recording"
        recorder_custom.recording_audio_record_number = 1
        recorder_custom.recording_audio_record_start_time = 1000.0
        
        result = recorder_custom._save_recording_audio_record()
        
        assert result == ""
    
    def test_stop_recording_not_recording(self, recorder_custom):
        """Test stopping recording when not recording."""
        result = recorder_custom.stop_recording()
        assert result == ""
    
    @patch('time.time')
    def test_stop_recording_with_timer(self, mock_time, recorder_custom):
        """Test stopping recording with active timer."""
        mock_time.return_value = 2000.0
        
        recorder_custom.is_recording = True
        recorder_custom.recording_start_time = 1000.0
        mock_timer = MagicMock()
        recorder_custom.recording_timer = mock_timer
        
        result = recorder_custom.stop_recording()
        
        assert result == ""
        assert recorder_custom.is_recording is False
        mock_timer.cancel.assert_called_once()
        assert recorder_custom.recording_timer is None
    
    @patch('time.time')
    @patch('wave.open')
    @patch('pathlib.Path.stat')
    def test_stop_recording_continuous_with_frames(self, mock_stat, mock_wave_open, mock_time, recorder_custom, sample_audio_data):
        """Test stopping continuous recording with frames."""
        mock_time.return_value = 2000.0
        mock_stat.return_value.st_size = 1024 * 1024  # 1MB
        
        recorder_custom.is_recording = True
        recorder_custom.is_continuous_recording = True
        recorder_custom.recording_start_time = 1000.0
        recorder_custom.recording_frames = [sample_audio_data]
        recorder_custom.recording_base_filename = "test_recording"
        recorder_custom.recording_audio_record_number = 1
        recorder_custom.recording_audio_record_start_time = 1000.0
        
        mock_wf = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wf
        
        result = recorder_custom.stop_recording()
        
        assert result == str(recorder_custom.recordings_dir / "test_recording_001.wav")
        assert recorder_custom.is_recording is False
    
    @patch('time.time')
    @patch('wave.open')
    @patch('pathlib.Path.stat')
    def test_stop_recording_duration_based_with_frames(self, mock_stat, mock_wave_open, mock_time, recorder_custom, sample_audio_data):
        """Test stopping duration-based recording with frames."""
        mock_time.return_value = 2000.0
        mock_stat.return_value.st_size = 1024 * 1024  # 1MB
        
        recorder_custom.is_recording = True
        recorder_custom.is_continuous_recording = False
        recorder_custom.recording_start_time = 1000.0
        recorder_custom.recording_frames = [sample_audio_data]
        recorder_custom.recording_base_filename = "test_recording"
        
        mock_wf = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wf
        
        result = recorder_custom.stop_recording()
        
        assert result == str(recorder_custom.recordings_dir / "test_recording.wav")
        assert recorder_custom.is_recording is False
    
    @patch('time.time')
    @patch('wave.open')
    def test_stop_recording_duration_based_exception(self, mock_wave_open, mock_time, recorder_custom, sample_audio_data):
        """Test stopping duration-based recording with exception."""
        mock_time.return_value = 2000.0
        mock_wave_open.side_effect = Exception("File write error")
        
        recorder_custom.is_recording = True
        recorder_custom.is_continuous_recording = False
        recorder_custom.recording_start_time = 1000.0
        recorder_custom.recording_frames = [sample_audio_data]
        recorder_custom.recording_base_filename = "test_recording"
        
        result = recorder_custom.stop_recording()
        
        assert result == ""
        assert recorder_custom.is_recording is False
    
    @patch('time.time')
    def test_get_recording_status_not_recording(self, mock_time, recorder_custom):
        """Test getting recording status when not recording."""
        mock_time.return_value = 2000.0
        
        status = recorder_custom.get_recording_status()
        
        expected = {
            "is_recording": False,
            "is_continuous": False,
            "base_filename": None,
            "total_duration": None,
            "current_audio_record_duration": None,
            "current_audio_record_number": 1,
            "frame_count": 0,
        }
        assert status == expected
    
    @patch('time.time')
    def test_get_recording_status_recording(self, mock_time, recorder_custom, sample_audio_data):
        """Test getting recording status when recording."""
        mock_time.return_value = 2000.0
        
        recorder_custom.is_recording = True
        recorder_custom.is_continuous_recording = True
        recorder_custom.recording_start_time = 1000.0
        recorder_custom.recording_audio_record_start_time = 1500.0
        recorder_custom.recording_base_filename = "test_recording"
        recorder_custom.recording_audio_record_number = 2
        recorder_custom.recording_frames = [sample_audio_data, sample_audio_data]
        
        status = recorder_custom.get_recording_status()
        
        expected = {
            "is_recording": True,
            "is_continuous": True,
            "base_filename": "test_recording",
            "total_duration": 1000.0,
            "current_audio_record_duration": 500.0,
            "current_audio_record_number": 2,
            "frame_count": 2,
        }
        assert status == expected
    
    def test_cleanup_not_recording(self, recorder_custom):
        """Test cleanup when not recording."""
        recorder_custom.cleanup()
        # Should not raise any exceptions
    
    @patch('time.time')
    def test_cleanup_recording(self, mock_time, recorder_custom):
        """Test cleanup when recording."""
        mock_time.return_value = 2000.0
        
        recorder_custom.is_recording = True
        mock_timer = MagicMock()
        recorder_custom.recording_timer = mock_timer
        
        with patch.object(recorder_custom, 'stop_recording') as mock_stop:
            recorder_custom.cleanup()
            
            mock_stop.assert_called_once()
            mock_timer.cancel.assert_called_once()
            assert recorder_custom.recording_timer is None
    
    def test_cleanup_with_timer_only(self, recorder_custom):
        """Test cleanup with timer but not recording."""
        mock_timer = MagicMock()
        recorder_custom.recording_timer = mock_timer
        
        recorder_custom.cleanup()
        
        mock_timer.cancel.assert_called_once()
        assert recorder_custom.recording_timer is None
    
    @patch('time.time')
    @patch('wave.open')
    @patch('pathlib.Path.stat')
    def test_file_size_formatting_mb(self, mock_stat, mock_wave_open, mock_time, recorder_custom, sample_audio_data):
        """Test file size formatting in MB."""
        mock_time.return_value = 2000.0
        mock_stat.return_value.st_size = 2 * 1024 * 1024  # 2MB
        
        recorder_custom.recording_frames = [sample_audio_data]
        recorder_custom.recording_base_filename = "test_recording"
        recorder_custom.recording_audio_record_number = 1
        recorder_custom.recording_audio_record_start_time = 1000.0
        
        mock_wf = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wf
        
        result = recorder_custom._save_recording_audio_record()
        
        assert result == str(recorder_custom.recordings_dir / "test_recording_001.wav")
    
    @patch('time.time')
    @patch('wave.open')
    @patch('pathlib.Path.stat')
    def test_file_size_formatting_gb(self, mock_stat, mock_wave_open, mock_time, recorder_custom, sample_audio_data):
        """Test file size formatting in GB."""
        mock_time.return_value = 2000.0
        mock_stat.return_value.st_size = 2 * 1024 * 1024 * 1024  # 2GB
        
        recorder_custom.recording_frames = [sample_audio_data]
        recorder_custom.recording_base_filename = "test_recording"
        recorder_custom.recording_audio_record_number = 1
        recorder_custom.recording_audio_record_start_time = 1000.0
        
        mock_wf = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wf
        
        result = recorder_custom._save_recording_audio_record()
        
        assert result == str(recorder_custom.recordings_dir / "test_recording_001.wav")
    
    def test_audio_record_duration_calculation_none_start_time(self, recorder_custom, sample_audio_data):
        """Test audio record duration calculation when start time is None."""
        recorder_custom.recording_frames = [sample_audio_data]
        recorder_custom.recording_base_filename = "test_recording"
        recorder_custom.recording_audio_record_number = 1
        recorder_custom.recording_audio_record_start_time = None
        
        with patch('wave.open'), patch('pathlib.Path.stat') as mock_stat:
            # Mock the stat to return a proper file size
            mock_stat.return_value.st_size = 1024
            result = recorder_custom._save_recording_audio_record()
            
            assert result == str(recorder_custom.recordings_dir / "test_recording_001.wav")
    
    def test_total_duration_calculation_none_start_time(self, recorder_custom):
        """Test total duration calculation when start time is None."""
        recorder_custom.is_recording = True
        recorder_custom.recording_start_time = None
        
        with patch('time.time', return_value=2000.0):
            result = recorder_custom.stop_recording()
            
            assert result == ""
    
    def test_continuous_recording_summary_logging(self, recorder_custom):
        """Test continuous recording summary logging."""
        recorder_custom.is_recording = True
        recorder_custom.is_continuous_recording = True
        recorder_custom.recording_start_time = 1000.0
        recorder_custom.recording_audio_record_number = 3  # 2 completed records
        
        with patch('time.time', return_value=2000.0):
            result = recorder_custom.stop_recording()
            
            assert result == ""
            assert recorder_custom.is_recording is False
