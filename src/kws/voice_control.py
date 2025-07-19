from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
import logging
import threading
import time
from pathlib import Path
import numpy as np
import pyaudio
import contextlib
import os

from picovoice import Picovoice

from kws import IntentDispatcher
from task_interface import TaskInterface
from lights import ColorRGB
from utils import rename_thread

if TYPE_CHECKING:
    from typing import Any
    from task_interface import Task

# Configure logger
logger = logging.getLogger("kws_logger")

class VoiceControl(threading.Thread):
    """
    Handles voice control functionalities for the Hexapod robot.
    """

    def __init__(
            self,
            keyword_path: Path,
            context_path: Path,
            access_key: str,
            task_interface: TaskInterface,
            device_index: int,
            porcupine_sensitivity: float = 0.75,
            rhino_sensitivity: float = 0.25,
            print_context: bool = False) -> None:
        """
        Initialize the VoiceControl thread.

        Args:
            keyword_path (Path): Path to the wake word keyword file.
            context_path (Path): Path to the language context file.
            access_key (str): Access key for Picovoice services.
            task_interface (TaskInterface): Task interface instance.
            device_index (int): Index of the audio input device.
            porcupine_sensitivity (float, optional): Sensitivity for wake word detection.
            rhino_sensitivity (float, optional): Sensitivity for intent recognition.
            print_context (bool): Whether to print context information.
        """
        super().__init__(daemon=True)
        rename_thread(self, "VoiceControl")

        # Initialize thread control variables first
        self.stop_event = threading.Event()
        self.pause_lock = threading.Lock()
        # pause_event controls whether voice control is active or paused:
        # - When set (True): Voice control is active and processing audio
        # - When cleared (False): Voice control is paused and not processing audio
        # - Initial state is set (True) so voice control starts active
        self.pause_event = threading.Event()
        self.pause_event.set()

        logger.debug(f"Initializing VoiceControl with device_index={device_index}")

        # Store initialization parameters for reinitialization
        self.keyword_path = keyword_path
        self.context_path = context_path
        self.access_key = access_key
        self.task_interface = task_interface
        self.device_index = device_index
        self.porcupine_sensitivity = porcupine_sensitivity
        self.rhino_sensitivity = rhino_sensitivity
        self.print_context = print_context

        # Determine device index: use external if specified, else auto-detect ReSpeaker 6
        auto_device_index = device_index
        if device_index is None or device_index == -1:
            auto_device_index = self.find_respeaker6_index()
            logger.info(f"Found ReSpeaker 6 at index {auto_device_index}")
            logger.info(f"Available audio devices:")
            for idx, name in enumerate(self.get_available_devices()):
                logger.info(f"  [{idx}] {name}")
            if auto_device_index == -1:
                logger.warning("ReSpeaker 6 not found, using default device (-1)")
                auto_device_index = -1
        self.device_index = auto_device_index

        # Picovoice API callback
        def inference_callback(inference: Any) -> None:
            logger.debug("Picovoice inference callback triggered")
            return self._inference_callback(inference)

        self.picovoice = Picovoice(
            access_key=access_key,
            keyword_path=keyword_path,
            wake_word_callback=self._wake_word_callback,
            context_path=str(context_path),
            inference_callback=inference_callback,
            porcupine_sensitivity=porcupine_sensitivity,
            rhino_sensitivity=rhino_sensitivity,
        )

        # Store Picovoice frame length for audio processing
        self.frame_length = self.picovoice.frame_length

        self.context = self.picovoice.context_info
        self.task_interface.set_task_complete_callback(self.on_task_complete)
        # Task interface interrupted flag
        # This flag is used to indicate that the current task was interrupted by a wake word detection
        self.task_interface_interrupted = False
        self.intent_dispatcher = IntentDispatcher(self.task_interface)

        # Audio objects (initialized in run())
        self.pyaudio_instance = None
        self.audio_stream = None
        
        # Audio processing thread control
        self.audio_thread = None
        self.audio_stop_event = threading.Event()
        
        if self.print_context:
            self.print_context()
        
        logger.debug("VoiceControl thread initialized successfully")

    @staticmethod
    @contextlib.contextmanager
    def _suppress_alsa_warnings():
        """Context manager to suppress ALSA warnings at file descriptor level."""
        # Save original stderr file descriptor
        original_stderr_fd = os.dup(2)  # stderr is file descriptor 2
        
        # Open /dev/null for writing
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        
        try:
            # Redirect stderr to /dev/null at file descriptor level
            os.dup2(devnull_fd, 2)
            yield
        finally:
            # Restore original stderr
            os.dup2(original_stderr_fd, 2)
            
            # Close file descriptors
            os.close(devnull_fd)
            os.close(original_stderr_fd)

    @staticmethod
    def get_available_devices() -> list[str]:
        """
        Get list of available audio devices.
        
        Returns:
            list[str]: List of available audio device names
        """
        try:
            # Suppress ALSA warnings by redirecting stderr at file descriptor level
            with VoiceControl._suppress_alsa_warnings():
                p = pyaudio.PyAudio()
                devices = []
                for i in range(p.get_device_count()):
                    device_info = p.get_device_info_by_index(i)
                    if device_info['maxInputChannels'] > 0:  # Only input devices
                        devices.append(device_info['name'])
                p.terminate()
                return devices
        except Exception as e:
            logger.error(f"Error getting available devices: {e}")
            return []

    @staticmethod
    def find_respeaker6_index():
        """
        Search for the device index of ReSpeaker 6 in the available devices list.
        Returns the index if found, else returns -1.
        """
        try:
            devices = VoiceControl.get_available_devices()
            for idx, name in enumerate(devices):
                if 'seeed-8mic-voicecard' in name.lower():
                    return idx
        except Exception as e:
            logger.error(f"[VoiceControl] Could not search for ReSpeaker 6: {e}")
        return -1

    def _initialize_audio(self):
        """Initialize PyAudio and audio stream."""
        try:
            # Suppress ALSA warnings by redirecting stderr at file descriptor level
            with self._suppress_alsa_warnings():
                self.pyaudio_instance = pyaudio.PyAudio()
            
            device_info = self.pyaudio_instance.get_device_info_by_index(self.device_index)
            logger.debug(f"Using audio device: {device_info['name']}")
            
            frames_per_buffer = 512
            
            # Open stream - use 8 channels for ReSpeaker, extract first channel for Picovoice
            self.audio_stream = self.pyaudio_instance.open(
                rate=16000,
                format=pyaudio.paInt16,
                channels=8,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=frames_per_buffer
            )
            
            logger.debug(f"Audio stream opened successfully with frames_per_buffer={frames_per_buffer}")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            raise

    def _audio_processor(self):
        """Process audio in separate thread."""
        logger.debug("Audio processing thread started")
        
        try:
            while not self.audio_stop_event.is_set():
                # Only process audio if not paused and resources are available
                if self.pause_event.is_set() and self.audio_stream and self.picovoice:
                    try:
                        # Read audio data directly from PyAudio stream
                        data = self.audio_stream.read(512, exception_on_overflow=False)
                        
                        # Convert to numpy array
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        
                        # Extract first channel for Picovoice (8-channel to single channel)
                        if len(audio_array) >= 8:
                            first_channel = audio_array[::8]  # Take first channel
                        else:
                            first_channel = audio_array
                        
                        # Process with Picovoice
                        # If more data than Picovoice needs, process in chunks
                        if len(first_channel) >= self.frame_length:
                            # Process the exact frame length that Picovoice expects
                            pcm_data = first_channel[:self.frame_length].astype(np.int16)
                            self.picovoice.process(pcm_data)
                        else:
                            # If we have less data, pad with zeros (shouldn't happen with 512 frames)
                            pcm_data = np.zeros(self.frame_length, dtype=np.int16)
                            pcm_data[:len(first_channel)] = first_channel.astype(np.int16)
                            self.picovoice.process(pcm_data)
                    except Exception as e:
                        logger.error(f"Audio processing error: {e}")
                        # Brief pause on error to prevent tight error loops
                        time.sleep(0.01)
                else:
                    # If paused or resources not available, just sleep briefly
                    time.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Audio processing thread error: {e}")
        finally:
            logger.debug("Audio processing thread finished")

    def _cleanup_audio(self):
        """Clean up audio resources."""
        try:
            # Stop audio processing thread first
            if self.audio_thread and self.audio_thread.is_alive():
                logger.debug("Stopping audio processing thread")
                self.audio_stop_event.set()
                self.audio_thread.join()
                self.audio_thread = None
            
            # Clean up audio stream
            if self.audio_stream:
                try:
                    logger.debug("Stopping audio stream")
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except Exception as e:
                    logger.warning(f"Error closing audio stream: {e}")
                finally:
                    self.audio_stream = None
                
            if self.pyaudio_instance:
                self.pyaudio_instance = None
                
        except Exception as e:
            logger.error(f"Error during audio cleanup: {e}")

    def print_context(self) -> None:
        """
        Prints the context information for debugging purposes.
        """
        print(self.context)

    def _wake_word_callback(self) -> None:
        """
        Callback function invoked when the wake word is detected.
        """
        logger.user_info('[wake word]')
        self.task_interface.lights_handler.listen_intent()

        if self.task_interface.task is not None:
            self.task_interface_interrupted = True
            logger.user_info(f"Interrupting current task: {self.task_interface.task.__class__.__name__}")
            self.task_interface.stop()

        logger.user_info("Listening for intent...")

    def _inference_callback(self, inference: Any) -> None:
        """
        Internal callback for handling inference results.

        Args:
            inference (Any): The inference result.
        """
        log_data = {
            "is_understood": inference.is_understood,
            "intent": inference.intent if inference.is_understood else None,
            "slots": inference.slots if inference.is_understood and inference.slots else None
        }
        logger.user_info(f"Inference Result: {log_data}")

        if inference.is_understood:
            self.intent_dispatcher.dispatch(inference.intent, inference.slots)
        else:
            logger.error("Inference not understood")
            self.task_interface.lights_handler.listen_wakeword(base_color=ColorRGB.RED, pulse_color=ColorRGB.GOLDEN)
            logger.user_info("Listening for wake word...")

    def on_task_complete(self, task: ControlTask) -> None:
        """
        Callback function invoked when a ControlTask completes.

        Args:
            task (ControlTask): The task that has completed.
        """
        logger.user_info(f"Voice control task {task.__class__.__name__} has been completed.")
        
        # Only set lights to listen for wake word if the voice control thread is still running
        if not self.stop_event.is_set() and not self.task_interface_interrupted:
            self.task_interface.lights_handler.listen_wakeword()
            logger.user_info("Listening for wake word...")
        else:
            logger.debug("Voice control thread is stopping, canceling the callback for wakeword listening (control task completed)")

        self.task_interface_interrupted = False

    def run(self) -> None:
        """
        Runs the voice control thread, initializing audio input and handling audio processing.
        """
        logger.debug("VoiceControl thread running")
        try:
            self.task_interface.voice_control_context_info = self.context

            # Initialize audio
            logger.debug("Initializing audio")
            self._initialize_audio()
            
            # Start audio processing thread (like interactive test)
            logger.debug("Starting audio processing thread")
            self.audio_stop_event.clear()
            self.audio_thread = threading.Thread(target=self._audio_processor, daemon=True)
            self.audio_thread.start()
            
            self.task_interface.lights_handler.listen_wakeword()
            logger.user_info("Listening for wake word...")
            
            paused = False

            while not self.stop_event.is_set():
                if self.task_interface.external_control_paused_event.is_set() and not paused:
                    self.pause()
                    paused = True
                elif not self.task_interface.external_control_paused_event.is_set() and paused:
                    self.unpause()
                    paused = False
                
                # Main thread just handles pause/unpause logic
                # Audio processing happens in separate thread
                time.sleep(0.1)

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
        
        finally:
            try:
                self._cleanup_audio()
                if self.picovoice is not None:
                    self.picovoice.delete()
                    self.picovoice = None
            except Exception as e:
                logger.exception(f"Error during cleanup: {e}")
            logger.debug("VoiceControl thread finished")

    def pause(self) -> None:
        """
        Pauses the voice control processing and releases the audio device.
        """
        with self.pause_lock:
            self.pause_event.clear()
            
            # Stop audio processing thread
            if self.audio_thread and self.audio_thread.is_alive():
                logger.debug("Stopping audio processing thread")
                self.audio_stop_event.set()
                self.audio_thread.join()
                self.audio_thread = None
            
            # Clean up audio resources manually
            if self.audio_stream:
                try:
                    logger.debug("Stopping audio stream")
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except Exception as e:
                    logger.warning(f"Error closing audio stream during pause: {e}")
                finally:
                    self.audio_stream = None
                    
            if self.pyaudio_instance:
                try:
                    logger.debug("Clearing PyAudio reference during pause (not terminating)")
                    self.pyaudio_instance = None
                except Exception as e:
                    logger.warning(f"Error clearing PyAudio reference during pause: {e}")
            
            # Release Picovoice resources - resets Picovoice object so that it doesn't process the same audio data again (pausing mid-command)
            if self.picovoice:
                try:
                    logger.debug("Deleting Picovoice resources")
                    self.picovoice.delete()
                except Exception as e:
                    logger.warning(f"Error deleting Picovoice during pause: {e}")
                finally:
                    self.picovoice = None
                    
            logger.user_info('Voice control paused')
            self.task_interface.lights_handler.off()

    def unpause(self) -> None:
        """
        Unpauses the voice control processing and reinitializes the audio device.
        """
        with self.pause_lock:
            # Reinitialize audio
            self._initialize_audio()
            
            # Start audio processing thread
            logger.debug("Starting audio processing thread")
            self.audio_stop_event.clear()
            self.audio_thread = threading.Thread(target=self._audio_processor, daemon=True)
            self.audio_thread.start()
            
            # Reinitialize Picovoice
            if not self.picovoice:
                self.picovoice = Picovoice(
                    access_key=self.access_key,
                    keyword_path=self.keyword_path,
                    wake_word_callback=self._wake_word_callback,
                    context_path=str(self.context_path),
                    inference_callback=self._inference_callback,
                    porcupine_sensitivity=self.porcupine_sensitivity,
                    rhino_sensitivity=self.rhino_sensitivity,
                )
            self.pause_event.set()
            logger.user_info('Voice control unpaused')
            self.task_interface.lights_handler.listen_wakeword()

    def stop(self):
        """Signal the thread to stop."""
        self.stop_event.set()
        logger.user_info('Voice control thread stopped')