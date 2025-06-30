from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Callable
import logging
import threading
from pathlib import Path
import numpy as np

from picovoice import Picovoice
from pvrecorder import PvRecorder
# from odas import ODASVoiceInput

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
            porcupine_sensitivity: float = 0.75,
            rhino_sensitivity: float = 0.25,
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
            porcupine_sensitivity (float, optional): Sensitivity for wake word detection.
            rhino_sensitivity (float, optional): Sensitivity for intent recognition.
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

        # Initialize thread control variables first
        self.stop_event = threading.Event()
        self.pause_lock = threading.Lock()
        self.pause_event = threading.Event()
        self.pause_event.set()

        logger.debug(f"Initializing VoiceControl with device_index={device_index}, use_odas={use_odas}")

        # Store initialization parameters for reinitialization
        self.keyword_path = keyword_path
        self.context_path = context_path
        self.access_key = access_key
        self.control_interface = control_interface
        self.device_index = device_index
        self.porcupine_sensitivity = porcupine_sensitivity
        self.rhino_sensitivity = rhino_sensitivity
        self.use_odas = use_odas
        self.odas_dir = odas_dir
        self.odas_channel = odas_channel
        self.log_dir = log_dir
        self.log_config_file = log_config_file
        self.clean = clean
        self.print_context = print_context

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

        # Store Picovoice frame length for PvRecorder reinitialization
        self.frame_length = self.picovoice.frame_length

        self.context = self.picovoice.context_info
        self.control_interface.set_task_complete_callback(self.on_task_complete)
        self.intent_dispatcher = IntentDispatcher(self.control_interface)

        if use_odas:
            if not odas_dir:
                raise ValueError("When using ODAS, odas_dir must be provided")
            
            logger.debug(f"Using ODAS for audio input from {odas_dir}")
            # Initialize ODAS voice input with Picovoice-compatible settings
            # self.odas_input = ODASVoiceInput(
            #     odas_dir=odas_dir,
            #     selected_channel=odas_channel,
            #     frame_length=self.picovoice.frame_length)
            # # Set up audio callback
            # self.odas_input.set_audio_callback(self._process_audio)
        else:
            logger.debug(f"Using PvRecorder for audio input with device_index={device_index}")
            # Initialize PvRecorder
            self.recorder = PvRecorder(device_index=device_index, frame_length=self.picovoice.frame_length)
        
        # Set up logging
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            if self.clean:
                for log_file in self.log_dir.glob("*.log"):
                    log_file.unlink()
            if self.log_config_file:
                logging.config.fileConfig(self.log_config_file)
                
        if self.print_context:
            self.print_context()
        
        logger.debug("VoiceControl thread initialized successfully")

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
        
        # Only set lights to listen for wake word if the voice control thread is still running
        if not self.stop_event.is_set():
            self.control_interface.lights_handler.listen_wakeword()
            logger.user_info("Listening for wake word...")
        else:
            logger.debug("Voice control thread is stopping, canceling the callback for wakeword listening (control task completed)")

    def run(self) -> None:
        """
        Runs the voice control thread, initializing audio input and handling audio processing.
        """
        logger.debug("VoiceControl thread running")
        try:
            self.control_interface.voice_control_context_info = self.context

            if self.use_odas:
                if not self.odas_dir:
                    raise ValueError("When using ODAS, odas_dir must be provided")
                logger.debug(f"Using ODAS for audio input from {self.odas_dir}")
                # Initialize ODAS voice input with Picovoice-compatible settings
                # self.odas_input = ODASVoiceInput(
                #     odas_dir=self.odas_dir,
                #     selected_channel=self.odas_channel,
                #     frame_length=self.frame_length)
                # # Set up audio callback
                # self.odas_input.set_audio_callback(self._process_audio)
                # # Start ODAS audio input
                # logger.debug("Starting ODAS audio input")
                # self.odas_input.start()
            else:
                # Start PvRecorder
                logger.debug("Starting PvRecorder")
                self.recorder.start()
                # rename_thread(self.recorder._thread, "PvRecorder")
            
            self.control_interface.lights_handler.listen_wakeword()
            logger.user_info("Listening for wake word...")
            
            paused = False

            while not self.stop_event.is_set():
                if self.control_interface.external_control_paused_event.is_set() and not paused:
                    self.pause()
                    paused = True
                elif not self.control_interface.external_control_paused_event.is_set() and paused:
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
            try:
                if self.use_odas:
                    logger.debug("Stopping ODAS audio input")
                    # if self.odas_input:
                    #     self.odas_input.stop()
                else:
                    if self.recorder and self.recorder.is_recording:
                        logger.debug("Stopping PvRecorder")
                        self.recorder.stop()
                    if self.recorder is not None:
                        self.recorder.delete()
                if self.picovoice is not None:
                    self.picovoice.delete()
            except Exception as e:
                logger.exception(f"Error during cleanup: {e}")
            logger.debug("VoiceControl thread finished")

    def _process_audio(self, audio_data: np.ndarray) -> None:
        """
        Process audio data from ODAS through Picovoice.

        Args:
            audio_data (np.ndarray): Audio data from ODAS
        """
        if self.pause_event.is_set():
            logger.debug(f"Processing audio frame of length {len(audio_data)}")
            self.picovoice.process(audio_data)

    def pause(self) -> None:
        """
        Pauses the voice control processing and releases the audio device.
        """
        with self.pause_lock:
            self.pause_event.clear()
            if self.use_odas:
                # Stop and clean up ODAS resources
                logger.debug("Stopping ODAS audio input")
                # if self.odas_input:
                #     self.odas_input.stop()
                #     self.odas_input = None
            else:
                if self.recorder:
                    if self.recorder.is_recording:
                        logger.debug("Stopping PvRecorder")
                        self.recorder.stop()
                    logger.debug("Deleting PvRecorder")
                    self.recorder.delete()  # Release the audio device - it is needed to wait (for other threads) for ~4 seconds to release resources by PvRecorder
                    self.recorder = None
            # Release Picovoice resources - resets Picovoice object so that it doesn't process the same audio data again (pausing mid-command)
            if self.picovoice:
                logger.debug("Deleting Picovoice resources")
                self.picovoice.delete()
                self.picovoice = None
            logger.user_info('Voice control paused')

    def unpause(self) -> None:
        """
        Unpauses the voice control processing and reinitializes the audio device.
        """
        with self.pause_lock:
            if self.use_odas:
                if not self.odas_dir:
                    raise ValueError("When using ODAS, odas_dir must be provided")
                logger.debug(f"Reinitializing ODAS audio input from {self.odas_dir}")
                # Initialize ODAS voice input with Picovoice-compatible settings
                # self.odas_input = ODASVoiceInput(
                #     odas_dir=self.odas_dir,
                #     selected_channel=self.odas_channel,
                #     frame_length=self.frame_length)
                # # Set up audio callback
                # self.odas_input.set_audio_callback(self._process_audio)
                # self.odas_input.start()
            else:
                # Reinitialize PvRecorder
                self.recorder = PvRecorder(device_index=self.device_index, frame_length=self.frame_length)
                self.recorder.start()
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
            self.control_interface.lights_handler.listen_wakeword()

    def stop(self):
        """Signal the thread to stop."""
        self.stop_event.set()
        if not self.use_odas and self.recorder and self.recorder.is_recording:
            self.recorder.stop()
        logger.user_info('Voice control thread stopped')