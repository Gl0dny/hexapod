import os
import argparse
import threading
import sys
import logging
from robot.hexapod import PredefinedPosition, PredefinedAnglePosition

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picovoice import Picovoice
from pvrecorder import PvRecorder
from intent_dispatcher import IntentDispatcher
from control import ControlInterface, StateManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceControl(threading.Thread):
    def __init__(
            self,
            keyword_path,
            context_path,
            access_key,
            device_index,
            porcupine_sensitivity=0.75,
            rhino_sensitivity=0.25):
        super(VoiceControl, self).__init__()

        # Picovoice API callback
        def inference_callback(inference):
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

    def print_context(self):
        print(self.context)

    def _wake_word_callback(self):
        print('[wake word]\n')
        self.control_interface.lights_handler.listen()
        self.control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

    def _inference_callback(self, inference):

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

    def run(self):
        recorder = None

        try:
            self.control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

            recorder = PvRecorder(device_index=self.device_index, frame_length=self.picovoice.frame_length)
            recorder.start()

            print('[Listening ...]')
            self.control_interface.lights_handler.ready()

            while True:
                pcm = recorder.read()
                self.picovoice.process(pcm)

                # Check for MaestroUART errors
                # controller_error_code = self.control_interface.hexapod.controller.get_error()
                # if controller_error_code != 0:
                #     print(f"Controller error: {controller_error_code}")
                    # self.control_interface.stop_control_task()
                    # # self.control_interface.lights_handler.set_single_color(ColorRGB.RED)
                    # self.control_interface.hexapod.deactivate_all_servos()
                    # break

        except KeyboardInterrupt:
            sys.stdout.write('\b' * 2)
            print("  ", flush=True)
            print('Stopping all tasks and deactivating hexapod due to keyboard interrupt...')
            self.control_interface.stop_control_task()
        finally:
            self.control_interface.lights_handler.off()
            self.control_interface.hexapod.deactivate_all_servos()

            if recorder is not None:
                recorder.delete()

            self.picovoice.delete()
            # self.control_interface.hexapod.controller.close()


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
    parser.add_argument(
        '--print_context',
        action='store_true',
        help='Print the context information.'
    )
    args = parser.parse_args()

    keyword_path = os.path.join(os.path.dirname(__file__), 'porcupine/hexapod_en_raspberry-pi_v3_0_0.ppn')
    context_path = os.path.join(os.path.dirname(__file__), 'rhino/hexapod_en_raspberry-pi_v3_0_0.rhn')

    voice_control = VoiceControl(
        keyword_path=keyword_path,
        context_path=context_path,
        access_key=args.access_key,
        device_index=args.audio_device_index
    )
    
    if args.print_context:
        voice_control.print_context()
    voice_control.run()


if __name__ == '__main__':
    main()
