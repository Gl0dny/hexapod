import os
import argparse
import threading
import logging

from picovoice import Picovoice
from central_dispatcher import CentralDispatcher
from state_manager import StateManager
from control_module import ControlModule

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceControl:
    def __init__(self, keyword_path, context_path, access_key, audio_device_index):
        # Initialize Control Module
        self.control = ControlModule()

        # Initialize Dispatcher and State Manager
        self.dispatcher = CentralDispatcher(self.control)
        self.state_manager = StateManager()

        # Initialize Picovoice
        self.picovoice = Picovoice(
            access_key=access_key,
            keyword_path=keyword_path,
            context_path=context_path,
            inference_callback=self.inference_callback,
            device_index=audio_device_index
        )

    def inference_callback(self, inference):
        if inference.is_understood:
            intent = inference.intent
            slots = inference.slots
            logger.info(f"Intent detected: {intent} with slots {slots}")

            if self.state_manager.can_execute(intent):
                self.dispatcher.dispatch(intent, slots)
            else:
                logger.warning(f"Cannot execute '{intent}' while in state '{self.state_manager.state.name}'")
        else:
            logger.warning("Command not understood.")

    def run(self):
        logger.info("Starting Picovoice...")
        self.picovoice.start()

    def stop(self):
        logger.info("Stopping Picovoice...")
        self.picovoice.stop()
        self.picovoice.delete()

def main():
    parser = argparse.ArgumentParser(description="Hexapod Voice Control Interface")
    parser.add_argument(
        '--access_key',
        help='AccessKey obtained from Picovoice Console (https://console.picovoice.ai/)',
        required=True
    )
    parser.add_argument(
        '--audio_device_index',
        help='Index of input audio device.',
        type=int,
        default=-1
    )
    args = parser.parse_args()

    # Define paths to keyword and context files
    keyword_path = os.path.join(os.path.dirname(__file__), 'hexapod_en_raspberry-pi_v3_0_0.ppn')
    context_path = os.path.join(os.path.dirname(__file__), 'your_updated_context.rhn')

    # Initialize VoiceControl
    voice_control = VoiceControl(
        keyword_path=keyword_path,
        context_path=context_path,
        access_key=args.access_key,
        audio_device_index=args.audio_device_index
    )

    try:
        voice_control.run()
        # Keep the main thread alive to allow Picovoice to process audio
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Exiting...")
    finally:
        voice_control.stop()

if __name__ == '__main__':
    main()