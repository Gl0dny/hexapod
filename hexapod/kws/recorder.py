"""
RecordingPvRecorder - A drop-in replacement for PvRecorder with recording capabilities.

This class provides the same interface as PvRecorder but adds the ability to record audio
while processing it with Picovoice. It maintains compatibility with the existing VoiceControl class.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import time
import threading
import wave
from pathlib import Path
import logging

if TYPE_CHECKING:
    from typing import Optional, List

logger = logging.getLogger("kws_logger")


class Recorder:
    """
    Handles audio recording functionality with support for continuous recording
    with automatic audio record splitting and duration-based recording.
    """

    # Default configuration
    DEFAULT_RECORDINGS_DIR = Path("data/audio/recordings")
    AUDIO_RECORD_DURATION = 30 * 60  # 15 minutes in seconds
    SAMPLE_RATE = 16000
    CHANNELS = 8
    FORMAT = "paInt16"

    def __init__(self, recordings_dir: Optional[Path] = None):
        """
        Initialize the Recorder.

        Args:
            recordings_dir (Path, optional): Directory to save recordings.
                                           Defaults to DEFAULT_RECORDINGS_DIR.
        """
        self.recordings_dir = recordings_dir or self.DEFAULT_RECORDINGS_DIR
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

        # Recording state
        self.is_recording = False
        self.is_continuous_recording = False
        self.recording_frames: List[bytes] = []
        self.recording_start_time: Optional[float] = None
        self.recording_audio_record_start_time: Optional[float] = None
        self.recording_audio_record_number = 1
        self.recording_base_filename: Optional[str] = None
        self.recording_timer: Optional[threading.Timer] = None

    def start_recording(
        self, filename: str = None, duration: Optional[float] = None
    ) -> str:
        """
        Start recording audio to a file.

        Args:
            filename (str, optional): Custom filename (without extension)
            duration (float, optional): Recording duration in seconds. If None, records until stopped.

        Returns:
            str: The base filename where recording will be saved
        """
        # If already recording, save current recording and start new one
        if self.is_recording:
            logger.info(
                "Recording already in progress - saving current recording and starting new one"
            )
            self.stop_recording()

        # Generate base filename
        if filename:
            self.recording_base_filename = filename
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.recording_base_filename = timestamp

        # Start recording
        self.recording_frames = []
        self.recording_start_time = time.time()
        self.recording_audio_record_start_time = time.time()
        self.recording_audio_record_number = 1
        self.is_recording = True
        self.is_continuous_recording = duration is None or duration <= 0

        # Set up auto-stop timer if duration specified
        if duration and duration > 0:
            self.recording_timer = threading.Timer(duration, self.stop_recording)
            self.recording_timer.daemon = True
            self.recording_timer.start()
            logger.info(
                f"Started recording to: {self.recording_base_filename}.wav (auto-stop in {duration}s)"
            )
        else:
            self.recording_timer = None
            logger.info(
                f"Started continuous recording to: {self.recording_base_filename}_001.wav (15-min audio records)"
            )

        return self.recording_base_filename

    def add_audio_frame(self, audio_data: bytes) -> None:
        """
        Add an audio frame to the current recording.

        Args:
            audio_data (bytes): Raw audio data to add to recording
        """
        if not self.is_recording:
            return

        self.recording_frames.append(audio_data)

        # Check if we need to save an audio record (for continuous recordings)
        if self.is_continuous_recording:
            current_time = time.time()
            audio_record_duration = (
                current_time - self.recording_audio_record_start_time
            )

            if audio_record_duration >= self.AUDIO_RECORD_DURATION:
                logger.info(
                    f"Audio record {self.recording_audio_record_number} duration reached ({audio_record_duration:.1f}s), saving..."
                )
                self._save_recording_audio_record()

    def _save_recording_audio_record(self) -> str:
        """
        Save the current recording audio record and start a new one.

        Returns:
            str: Path to the saved audio record file
        """
        if not self.recording_frames:
            logger.warning("No audio frames to save in audio record")
            return ""

        # Generate audio record filename
        audio_record_filename = f"{self.recording_base_filename}_{self.recording_audio_record_number:03d}.wav"
        recording_path = self.recordings_dir / audio_record_filename

        try:
            with wave.open(str(recording_path), "wb") as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(b"".join(self.recording_frames))

            audio_record_duration = time.time() - self.recording_audio_record_start_time
            file_size = recording_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            if file_size_mb >= 1024:
                file_size_str = f"{file_size_mb/1024:.1f} GB"
            else:
                file_size_str = f"{file_size_mb:.1f} MB"
            logger.user_info(
                f"Audio record {self.recording_audio_record_number} saved: {recording_path} (Duration: {audio_record_duration:.1f}s, Size: {file_size_str})"
            )

            # Reset for next audio record
            self.recording_frames = []
            self.recording_audio_record_start_time = time.time()
            self.recording_audio_record_number += 1

            return str(recording_path)

        except Exception as e:
            logger.error(f"Failed to save recording audio record: {e}")
            return ""

    def stop_recording(self) -> str:
        """
        Stop recording and save the audio file.

        Returns:
            str: Path to the last saved recording file, or empty string if no recording was active
        """
        if not self.is_recording:
            logger.warning("No recording in progress")
            return ""

        # Cancel auto-stop timer if it exists
        if self.recording_timer:
            self.recording_timer.cancel()
            self.recording_timer = None

        self.is_recording = False
        total_duration = time.time() - self.recording_start_time

        # Save final audio record if there are frames
        last_saved_file = ""
        if self.recording_frames:
            if self.is_continuous_recording:
                # For continuous recording, save as final audio record
                last_saved_file = self._save_recording_audio_record()
            else:
                # For duration-based recording, save as single file
                try:
                    recording_path = (
                        self.recordings_dir / f"{self.recording_base_filename}.wav"
                    )

                    with wave.open(str(recording_path), "wb") as wf:
                        wf.setnchannels(self.CHANNELS)
                        wf.setsampwidth(2)  # 16-bit = 2 bytes
                        wf.setframerate(self.SAMPLE_RATE)
                        wf.writeframes(b"".join(self.recording_frames))

                    file_size = recording_path.stat().st_size
                    file_size_mb = file_size / (1024 * 1024)
                    if file_size_mb >= 1024:
                        file_size_str = f"{file_size_mb/1024:.1f} GB"
                    else:
                        file_size_str = f"{file_size_mb:.1f} MB"
                    logger.user_info(
                        f"Recording finished and saved: {recording_path} (Duration: {total_duration:.1f}s, Size: {file_size_str})"
                    )
                    last_saved_file = str(recording_path)

                except Exception as e:
                    logger.error(f"Failed to save recording: {e}")
                    return ""

        # Log summary for continuous recordings
        if self.is_continuous_recording:
            total_audio_records = self.recording_audio_record_number - 1
            logger.user_info(
                f"Continuous recording finished. Total duration: {total_duration:.1f}s, Total audio records: {total_audio_records}"
            )

        return last_saved_file

    def get_recording_status(self) -> dict:
        """
        Get current recording status.

        Returns:
            dict: Status information including is_recording, filename, duration, audio records
        """
        duration = None
        audio_record_duration = None

        if self.recording_start_time and self.is_recording:
            duration = time.time() - self.recording_start_time

        if self.recording_audio_record_start_time and self.is_recording:
            audio_record_duration = time.time() - self.recording_audio_record_start_time

        return {
            "is_recording": self.is_recording,
            "is_continuous": self.is_continuous_recording,
            "base_filename": self.recording_base_filename,
            "total_duration": duration,
            "current_audio_record_duration": audio_record_duration,
            "current_audio_record_number": self.recording_audio_record_number,
            "frame_count": len(self.recording_frames) if self.recording_frames else 0,
        }

    def cleanup(self) -> None:
        """
        Clean up recording resources.
        """
        if self.is_recording:
            self.stop_recording()

        if self.recording_timer:
            self.recording_timer.cancel()
            self.recording_timer = None
