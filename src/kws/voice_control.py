from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import threading
from pathlib import Path

from picovoice import Picovoice
from pvrecorder import PvRecorder

from kws import IntentDispatcher
from control import ControlInterface
from lights import ColorRGB
from utils import rename_thread

if TYPE_CHECKING:
    from typing import Any
    from control import ControlTask

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
            device_index: int,
            control_interface: ControlInterface,
            porcupine_sensitivity: float = 0.75,
            rhino_sensitivity: float = 0.25) -> None:
        """
        Initialize the VoiceControl thread.

        Args:
            keyword_path (Path): Path to the wake word keyword file.
            context_path (Path): Path to the language context file.
            access_key (str): Access key for Picovoice services.
            device_index (int): Index of the audio input device.
            control_interface (ControlInterface): Control interface instance.
            porcupine_sensitivity (float, optional): Sensitivity for wake word detection.
            rhino_sensitivity (float, optional): Sensitivity for intent recognition.
        """
        super().__init__(daemon=True)
        rename_thread(self, "VoiceControl")

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
            rhino_sensitivity=rhino_sensitivity)

        self.context = self.picovoice.context_info
        self.device_index = device_index

        self.control_interface = control_interface
        self.control_interface.set_task_complete_callback(self.on_task_complete)

        self.intent_dispatcher = IntentDispatcher(self.control_interface)

        self.recorder = None
        self.stop_event = threading.Event()
        self.pause_lock = threading.Lock()
        self.pause_event = threading.Event()
        self.pause_event.set()

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
        self.control_interface.lights_handler.listen_wakeword()
        logger.user_info("Listening for wake word...")

    def pause(self) -> None:
        """
        Pauses the voice control processing.
        """
        with self.pause_lock:
            self.pause_event.clear()
            if self.recorder and self.recorder.is_recording:
                self.recorder.stop()
            logger.user_info('Voice control paused')

    def unpause(self) -> None:
        """
        Unpauses the voice control processing.
        """
        with self.pause_lock:
            if self.recorder and not self.recorder.is_recording:
                self.recorder.start()
            self.pause_event.set()
            logger.user_info('Voice control unpaused')
            self.control_interface.lights_handler.listen_wakeword()

    def stop(self):
        """Signal the thread to stop."""
        self.stop_event.set()
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()
            logger.user_info('Voice control thread stopped')

    def run(self) -> None:
        """
        Runs the voice control thread, initializing Picovoice and handling audio input.
        """
        logger.debug("VoiceControl thread running")
        try:
            self.control_interface.voice_control_context_info = self.context

            self.recorder = PvRecorder(device_index=self.device_index, frame_length=self.picovoice.frame_length)
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
                if self.pause_event.wait(timeout=0.1):
                    pcm = self.recorder.read()
                    self.picovoice.process(pcm)

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
        
        finally:
            if self.recorder and self.recorder.is_recording:
                self.recorder.stop()

            if self.recorder is not None:
                self.recorder.delete()

            self.picovoice.delete()
            
            logger.debug("VoiceControl thread finished")