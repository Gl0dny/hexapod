import os
import threading
import sys
import logging
from typing import Callable, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picovoice import Picovoice
from pvrecorder import PvRecorder
from kws.intent_dispatcher import IntentDispatcher
from control import ControlInterface, StateManager
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
            porcupine_sensitivity: float = 0.75,
            rhino_sensitivity: float = 0.25) -> None:
        """
        Initialize the VoiceControl thread.

        Args:
            keyword_path (str): Path to the wake word keyword file.
            context_path (str): Path to the language context file.
            access_key (str): Access key for Picovoice services.
            device_index (int): Index of the audio input device.
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

        self.control_interface = ControlInterface(voice_control_context_info=self.context)
        self.intent_dispatcher = IntentDispatcher(self.control_interface)
        # self.state_manager = StateManager()

        self._stop_event = threading.Event()

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
            # if self.state_manager.can_execute(inference.intent):
                # self.control_interface.lights_handler.think()
                self.intent_dispatcher.dispatch(inference.intent, inference.slots)
            # else:
            #     logger.warning(f"Cannot execute '{inference.intent}' while in state '{self.state_manager.state.name}'")

                # self.control_interface.lights_handler.off()
                print('\n[Listening ...]')
        else:
            self.control_interface.lights_handler.ready()

    def stop(self):
        """Signal the thread to stop."""
        print('Stopping voice control thread...')
        self._stop_event.set()

    def run(self) -> None:
        """
        Runs the voice control thread, initializing Picovoice and handling audio input.
        """
        recorder = None

        try:
            self.control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

            recorder = PvRecorder(device_index=self.device_index, frame_length=self.picovoice.frame_length)
            recorder.start()

            print('[Listening ...]')
            self.control_interface.lights_handler.ready()

            while not self._stop_event.is_set():
                pcm = recorder.read()
                self.picovoice.process(pcm)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        finally:
            self.control_interface.stop_control_task()
            self.control_interface.lights_handler.off()
            self.control_interface.hexapod.deactivate_all_servos()

            if recorder is not None:
                recorder.delete()

            self.picovoice.delete()
            
            print('Voice control thread stopped.')