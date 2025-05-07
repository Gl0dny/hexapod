from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
import logging
import threading
from pathlib import Path
import numpy as np

from picovoice import Picovoice
from pvrecorder import PvRecorder
from odas import ODASVoiceInput

from kws import IntentDispatcher
from control import ControlInterface
from lights import ColorRGB
from utils import rename_thread

if TYPE_CHECKING:
    from typing import Any
    from control import ControlTask

# Configure logger
logger = logging.getLogger("voice_control")

class VoiceControl(threading.Thread):
    """
    Handles voice control functionalities for the Hexapod robot.
    """

    def __init__(
            self,
            keyword_path: Path,
            context_path: Path,
            access_key: str,
            control_interface: ControlInterface,
            device_index: int,
            use_odas: bool = False,
            odas_dir: Optional[Path] = None,
            odas_channel: int = 0,
            log_dir: Optional[Path] = None,
            log_config_file: Optional[Path] = None,
            clean: bool = False,
            print_context: bool = False) -> None:
        """
        Initialize the VoiceControl thread.

        Args:
            keyword_path (Path): Path to the wake word keyword file.
            context_path (Path): Path to the language context file.
            access_key (str): Access key for Picovoice services.
            control_interface (ControlInterface): Control interface instance.
            device_index (int): Index of the audio input device for PvRecorder.
            use_odas (bool, optional): Whether to use ODAS for audio input.
            odas_dir (Optional[Path]): Directory where ODAS creates raw files.
            odas_channel (int): Which channel to use from the ODAS array.
            log_dir (Optional[Path]): Directory for log files.
            log_config_file (Optional[Path]): Path to log configuration file.
            clean (bool): Whether to clean log files before starting.
            print_context (bool): Whether to print context information.
        """
        super().__init__(daemon=True)
        rename_thread(self, "VoiceControl")

        print(f"[DEBUG] Initializing VoiceControl with device_index={device_index}, use_odas={use_odas}")

        # Picovoice API callback
        def inference_callback(inference: Any) -> None:
            print("[DEBUG] Picovoice inference callback triggered")
            return self._inference_callback(inference)

        self.picovoice = Picovoice(
            access_key=access_key,
            keyword_path=keyword_path,
            wake_word_callback=self._wake_word_callback,
            context_path=str(context_path),
            inference_callback=inference_callback,
            porcupine_sensitivity=0.75,
            rhino_sensitivity=0.25)

        self.context = self.picovoice.context_info
        self.device_index = device_index

        self.control_interface = control_interface
        self.control_interface.set_task_complete_callback(self.on_task_complete)

        self.intent_dispatcher = IntentDispatcher(self.control_interface)

        self.use_odas = use_odas
        if use_odas:
            if not odas_dir:
                raise ValueError("When using ODAS, odas_dir must be provided")
            
            print(f"[DEBUG] Using ODAS for audio input from {odas_dir}")
            # Initialize ODAS voice input with Picovoice-compatible settings
            self.odas_input = ODASVoiceInput(
                odas_dir=odas_dir,
                selected_channel=odas_channel,
                frame_length=self.picovoice.frame_length)
            # Set up audio callback
            self.odas_input.set_audio_callback(self._process_audio)
        else:
            print(f"[DEBUG] Using PvRecorder for audio input with device_index={device_index}")
            # Initialize PvRecorder
            self.recorder = PvRecorder(device_index=device_index, frame_length=self.picovoice.frame_length)
        
        self.stop_event = threading.Event()
        self.pause_lock = threading.Lock()
        self.pause_event = threading.Event()
        self.pause_event.set()

        # Set up logging
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            if clean:
                for log_file in log_dir.glob("*.log"):
                    log_file.unlink()
            if log_config_file:
                logging.config.fileConfig(log_config_file)
                
        if print_context:
            self.print_context()
        
        print("[DEBUG] VoiceControl thread initialized successfully")

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
        self.control_interface.lights_handler.listen_intent()
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
            self.control_interface.lights_handler.listen_wakeword(base_color=ColorRGB.RED, pulse_color=ColorRGB.GOLDEN)
            logger.user_info("Listening for wake word...")

    def on_task_complete(self, task: ControlTask) -> None:
        """
        Callback function invoked when a ControlTask completes.

        Args:
            task (ControlTask): The task that has completed.
        """
        logger.user_info(f"Voice control task {task.__class__.__name__} has been completed.")
        self.control_interface.lights_handler.listen_wakeword()
        logger.user_info("Listening for wake word...")

    def run(self) -> None:
        """
        Runs the voice control thread, initializing audio input and handling audio processing.
        """
        print("[DEBUG] VoiceControl thread running")
        try:
            self.control_interface.voice_control_context_info = self.context

            if self.use_odas:
                # Start ODAS audio input
                print("[DEBUG] Starting ODAS audio input")
                self.odas_input.start()
            else:
                # Start PvRecorder
                print("[DEBUG] Starting PvRecorder")
                self.recorder.start()
                # rename_thread(self.recorder._thread, "PvRecorder")
            
            self.control_interface.lights_handler.listen_wakeword()
            logger.user_info("Listening for wake word...")
            
            paused = False

            while not self.stop_event.is_set():
                if self.control_interface.maintenance_mode_event.is_set() and not paused:
                    self.pause()
                    paused = True
                elif not self.control_interface.maintenance_mode_event.is_set() and paused:
                    self.unpause()
                    paused = False
                
                if self.use_odas:
                    if not self.pause_event.wait(timeout=0.1):
                        continue
                else:
                    if self.pause_event.wait(timeout=0.1):
                        pcm = self.recorder.read()
                        self.picovoice.process(pcm)

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
        
        finally:
            if self.use_odas:
                print("[DEBUG] Stopping ODAS audio input")
                self.odas_input.stop()
            else:
                if self.recorder and self.recorder.is_recording:
                    print("[DEBUG] Stopping PvRecorder")
                    self.recorder.stop()
                if self.recorder is not None:
                    self.recorder.delete()
            self.picovoice.delete()
            print("[DEBUG] VoiceControl thread finished")

    def _process_audio(self, audio_data: np.ndarray) -> None:
        """
        Process audio data from ODAS through Picovoice.

        Args:
            audio_data (np.ndarray): Audio data from ODAS
        """
        if self.pause_event.is_set():
            print(f"[DEBUG] Processing audio frame of length {len(audio_data)}")
            self.picovoice.process(audio_data)

    def pause(self) -> None:
        """
        Pauses the voice control processing.
        """
        with self.pause_lock:
            self.pause_event.clear()
            if not self.use_odas and self.recorder and self.recorder.is_recording:
                self.recorder.stop()
            logger.user_info('Voice control paused')

    def unpause(self) -> None:
        """
        Unpauses the voice control processing.
        """
        with self.pause_lock:
            if not self.use_odas and self.recorder and not self.recorder.is_recording:
                self.recorder.start()
            self.pause_event.set()
            logger.user_info('Voice control unpaused')
            self.control_interface.lights_handler.listen_wakeword()

    def stop(self):
        """Signal the thread to stop."""
        self.stop_event.set()
        if not self.use_odas and self.recorder and self.recorder.is_recording:
            self.recorder.stop()
        logger.user_info('Voice control thread stopped')