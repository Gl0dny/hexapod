import argparse
import sys
import os
import time
from kws import VoiceControl
from lights import ColorRGB
from robot import PredefinedAnglePosition, PredefinedPosition
from control import ControlInterface, StateManager

def main() -> None:
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

    keyword_path = os.path.join(os.path.dirname(__file__), 'kws/porcupine/hexapod_en_raspberry-pi_v3_0_0.ppn')
    context_path = os.path.join(os.path.dirname(__file__), 'kws/rhino/hexapod_en_raspberry-pi_v3_0_0.rhn')

    control_interface = ControlInterface()
    # state_manager = StateManager()

    voice_control = VoiceControl(
        keyword_path=keyword_path,
        context_path=context_path,
        access_key=args.access_key,
        device_index=args.audio_device_index,
        control_interface=control_interface,
        # state_manager=state_manager
    )

    if args.print_context:
        voice_control.print_context()
        
    voice_control.start()  # Start VoiceControl as a separate thread

    try:
        # Check for MaestroUART errors
        while True:
            # controller_error_code = voice_control.control_interface.hexapod.controller.get_error()
            # if controller_error_code != 0:
            #     print(f"Controller error: {controller_error_code}")
            #     voice_control.pause()
            #     time.sleep(1)
            #     voice_control.control_interface.lights_handler.set_single_color(ColorRGB.RED)
            #     voice_control.control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            #     break
            time.sleep(1)
    except KeyboardInterrupt:
        sys.stdout.write('\b' * 2)
        print("  ", flush=True)
        print('Stopping all tasks and deactivating hexapod due to keyboard interrupt...')
        voice_control.stop()
        voice_control.join()
    finally:
        # voice_control.control_interface.hexapod.controller.close()
        print('Exiting...')

if __name__ == '__main__':
    main()