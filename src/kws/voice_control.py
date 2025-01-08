import os
import threading
import sys
import logging
from typing import Callable, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picovoice import Picovoice
from pvrecorder import PvRecorder
from kws.intent_dispatcher import IntentDispatcher
from control import ControlInterface
from robot.hexapod import PredefinedPosition, PredefinedAnglePosition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceControl(threading.Thread):
    """
    Handles voice control functionalities for the Hexapod robot.
    """

    def __init__(
            self,
            keyword_path: str,
            context_path: str,
            access_key: str,
            device_index: int,
            control_interface: ControlInterface,
            porcupine_sensitivity: float = 0.75,
            rhino_sensitivity: float = 0.25) -> None:
        """
        Initialize the VoiceControl thread.

        Args:
            keyword_path (str): Path to the wake word keyword file.
            context_path (str): Path to the language context file.
            access_key (str): Access key for Picovoice services.
            device_index (int): Index of the audio input device.
            control_interface (ControlInterface): Control interface instance.
            porcupine_sensitivity (float, optional): Sensitivity for wake word detection.
            rhino_sensitivity (float, optional): Sensitivity for intent recognition.
        """
        super(VoiceControl, self).__init__()

        # Picovoice API callback
        def inference_callback(inference: Any) -> None:
            return self._inference_callback(inference)

        self.picovoice = Picovoice(
            access_key=access_key,
            keyword_path=keyword_path,
            wake_word_callback=self._wake_word_callback,
            context_path=context_path,
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
        print(self.context)

    def _wake_word_callback(self) -> None:
        """
        Callback function invoked when the wake word is detected.
        """
        print('[wake word]\n')
        self.control_interface.lights_handler.listen()
        self.control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

    def _inference_callback(self, inference: Any) -> None:
        """
        Internal callback for handling inference results.

        Args:
            inference (Any): The inference result.
        """
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
            self.intent_dispatcher.dispatch(inference.intent, inference.slots)
            print('\n[Listening ...]')
        else:
            self.control_interface.lights_handler.ready()

    def pause(self) -> None:
        """
        Pauses the voice control processing.
        """
        with self.pause_lock:
            self.pause_event.clear()
            if self.recorder and self.recorder.is_recording:
                self.recorder.stop()
            self.control_interface.lights_handler.off()
            print('Voice control paused.')

    def unpause(self) -> None:
        """
        Unpauses the voice control processing.
        """
        with self.pause_lock:
            if self.recorder and not self.recorder.is_recording:
                self.recorder.start()
            self.control_interface.lights_handler.ready()
            self.pause_event.set()
            print('Voice control unpaused.')
            print('[Listening ...]')

    def stop(self):
        """Signal the thread to stop."""
        print('Stopping voice control thread...')
        self.stop_event.set()
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()

    def run(self) -> None:
        """
        Runs the voice control thread, initializing Picovoice and handling audio input.
        """
        try:
            self.control_interface.voice_control_context_info = self.context
            self.control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

            self.recorder = PvRecorder(device_index=self.device_index, frame_length=self.picovoice.frame_length)
            self.recorder.start()

            print('[Listening ...]')
            self.control_interface.lights_handler.ready()

            while not self.stop_event.is_set():
                if self.control_interface.shutdown_event.is_set():
                    self.pause()
                else:
                    if not self.pause_event.is_set():
                        self.unpause()
                if self.pause_event.wait(timeout=0.1):
                    pcm = self.recorder.read()
                    self.picovoice.process(pcm)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        finally:
            if self.recorder and self.recorder.is_recording:
                self.recorder.stop()
            self.control_interface.stop_control_task()
            self.control_interface.lights_handler.off()
            self.control_interface.hexapod.deactivate_all_servos()

            if self.recorder is not None:
                self.recorder.delete()

            self.picovoice.delete()
            
            print('Voice control thread stopped.')