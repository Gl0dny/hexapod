import os
import threading
import sys
import logging
from typing import Any
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picovoice import Picovoice
from pvrecorder import PvRecorder
from kws.intent_dispatcher import IntentDispatcher
from control import ControlInterface

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
        logger.debug("Initializing VoiceControl thread")
        super(VoiceControl, self).__init__()

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

        self.intent_dispatcher = IntentDispatcher(self.control_interface)

        self.recorder = None
        self.stop_event = threading.Event()
        self.pause_lock = threading.Lock()
        self.pause_event = threading.Event()
        self.pause_event.set()

    def print_context(self) -> None:
        """
        Prints the context information for debugging purposes.
        """
        logger.info("Printing context information")
        print(self.context)

    def _wake_word_callback(self) -> None:
        """
        Callback function invoked when the wake word is detected.
        """
        logger.info("Wake word detected")
        print('[wake word]\n')
        self.control_interface.lights_handler.listen()

    def _inference_callback(self, inference: Any) -> None:
        """
        Internal callback for handling inference results.

        Args:
            inference (Any): The inference result.
        """
        logger.debug(f"Inference received: {inference}")
        self.control_interface.lights_handler.off()

        print('{')
        print("  is_understood : '%s'," % ('true' if inference.is_understood else 'false'))
        if inference.is_understood:
            print("  intent : '%s'," % inference.intent)
            if len(inference.slots) > 0:
                print('  slots : {')
                for slot, value in inference.slots.items():
                    print("    '%s' : '%s'," % (slot, value))
                print('  }')
        print('}\n')

        if inference.is_understood:
            logger.info(f"Dispatching intent: {inference.intent} with slots: {inference.slots}")
            self.intent_dispatcher.dispatch(inference.intent, inference.slots)
        else:
            logger.info("Inference not understood, setting lights to ready")
            self.control_interface.lights_handler.ready()

    def pause(self) -> None:
        """
        Pauses the voice control processing.
        """
        with self.pause_lock:
            self.pause_event.clear()
            if self.recorder and self.recorder.is_recording:
                self.recorder.stop()
            logger.info('Voice control paused.')

    def unpause(self) -> None:
        """
        Unpauses the voice control processing.
        """
        with self.pause_lock:
            if self.recorder and not self.recorder.is_recording:
                self.recorder.start()
            self.pause_event.set()
            logger.info('Voice control unpaused.')
            self.control_interface.lights_handler.ready()

    def stop(self):
        """Signal the thread to stop."""
        logger.info('Stopping voice control thread...')
        self.stop_event.set()
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()
            logger.debug("Recorder stopped")

    def run(self) -> None:
        """
        Runs the voice control thread, initializing Picovoice and handling audio input.
        """
        logger.debug("VoiceControl thread started running")
        try:
            self.control_interface.voice_control_context_info = self.context

            self.recorder = PvRecorder(device_index=self.device_index, frame_length=self.picovoice.frame_length)
            self.recorder.start()

            self.control_interface.lights_handler.ready()
            
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
            logger.error(f"Unexpected error: {e}")
        
        finally:
            if self.recorder and self.recorder.is_recording:
                self.recorder.stop()

            if self.recorder is not None:
                self.recorder.delete()

            self.picovoice.delete()
            
            print('Voice control thread stopped.')
            logger.info("VoiceControl thread exiting")