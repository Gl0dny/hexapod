import argparse
import sys
import time
import logging.config
import pathlib
import json
import atexit

from src.kws import VoiceControl
from src.control import ControlInterface
from src.lights import ColorRGB
from src.robot import PredefinedAnglePosition, PredefinedPosition
from pathlib import Path
from src.utils import logger

logger = logging.getLogger(__name__)

def setup_logging() -> None:
    config_file = pathlib.Path("logs/config.json")
    if config_file.is_file():
        with open(config_file, "rt") as f:
            logging.config.dictConfig(json.load(f))
        queue_handler = logging.getHandlerByName("queue_handler")
        if queue_handler is not None:
            queue_handler.listener.start()
            atexit.register(queue_handler.listener.stop)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.warning(f"Logging configuration file not found at {config_file}")

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hexapod Robot Controller")
    parser.add_argument("--access_key", type=str, required=True, help="Picovoice Access Key")
    parser.add_argument("--audio_device_index", type=int, default=-1, help="Audio device index")
    parser.add_argument('--print_context', action='store_true', help='Print the context information.')
    return parser.parse_args()

def main() -> None:

    setup_logging()

    args = parse_arguments()

    keyword_path = Path('src/kws/porcupine/hexapod_en_raspberry-pi_v3_0_0.ppn')
    context_path = Path('src/kws/rhino/hexapod_en_raspberry-pi_v3_0_0.rhn')

    control_interface = ControlInterface()

    control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

    voice_control = VoiceControl(
        keyword_path=keyword_path,
        context_path=context_path,
        access_key=args.access_key,
        device_index=args.audio_device_index,
        control_interface=control_interface,
    )

    if args.print_context:
        voice_control.print_context()
        
    voice_control.start()  # Start VoiceControl as a separate thread

    try:
        # Check for MaestroUART errors
        while True:
            # controller_error_code = control_interface.hexapod.controller.get_error()
            # if controller_error_code != 0:
            #     print(f"Controller error: {controller_error_code}")
            #     voice_control.pause()
            #     time.sleep(1)
            #     control_interface.lights_handler.set_single_color(ColorRGB.RED)
            #     control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            #     break
            time.sleep(1)
    except KeyboardInterrupt:
        sys.stdout.write('\b' * 2)
        print("  ", flush=True)
        print('Stopping all tasks and deactivating hexapod due to keyboard interrupt...')
        control_interface.stop_control_task()
        voice_control.stop()
        voice_control.join()
        control_interface.lights_handler.off()
    finally:
        time.sleep(5)
        control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
        control_interface.hexapod.deactivate_all_servos()
        # control_interface.hexapod.controller.close()
        print('Exiting...')

if __name__ == '__main__':
    main()