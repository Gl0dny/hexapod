import argparse
import sys
import time
import logging.config
import yaml
import atexit
import threading
from pathlib import Path
from typing import Optional

from src.interface import logger
from src.kws import VoiceControl
from src.control import ControlInterface
from src.lights import ColorRGB
from src.robot import PredefinedAnglePosition, PredefinedPosition
from src.utils import rename_thread

logger = logging.getLogger("main_logger")

def setup_logging(log_dir: Optional[Path] = None, config_file: Optional[Path] = None) -> None:
    if config_file is None:
        log_dir = Path("logs")
    
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    if config_file is None:
        config_file = log_dir / "config.yaml"

    if config_file.is_file():
        with open(config_file, "rt") as f:
            config = yaml.safe_load(f)
        
        # Update handler filenames to use the provided log_dir
        for handler_name, handler in config.get("handlers", {}).items():
            filename = handler.get("filename")
            if filename:
                handler["filename"] = str(log_dir / Path(filename).name)  # Set to log_dir/<basename>
        
        logging.config.dictConfig(config)
        queue_handler = logging.getLogger("root").handlers[0]  # Assuming queue_handler is the first handler
        if queue_handler is not None and hasattr(queue_handler, 'listener'):
            queue_handler.listener.start()
            rename_thread(queue_handler.listener._thread, "QueueHandlerListener")
            atexit.register(queue_handler.listener.stop)
    else:
        logging.basicConfig(level=logging.INFO)
        logger.warning(f"Logging configuration file not found at {config_file}. Using basic logging configuration")

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hexapod Robot Controller")
    parser.add_argument("--access_key", type=str, required=True, help="Picovoice Access Key")
    parser.add_argument("--audio_device_index", type=int, default=-1, help="Audio device index")
    parser.add_argument('--print_context', action='store_true', help='Print the context information.')
    parser.add_argument('--clean', '-c', action='store_true', help='Clean all logs in the logs directory.')
    parser.add_argument('--log_dir', type=Path, default=Path("logs"), help='Directory for log files.')
    parser.add_argument('--log_config_file', type=Path, default=Path("logs/config.yaml"), help='Path to logging configuration yaml/json file.')
    args = parser.parse_args()
    return args

def clean_logs() -> None:
    project_dir = Path(__file__).parent
    log_patterns = ['*.log', '*.log.jsonl']
    for pattern in log_patterns:
        for log_file in project_dir.rglob(pattern):
            log_file.unlink()

def main() -> None:
    args = parse_arguments()

    if args.clean:
        clean_logs()

    setup_logging(log_dir=args.log_dir, config_file=args.log_config_file)

    logger.user_info("Application started")

    # for thread in threading.enumerate():
    #     logger.user_info(f"{thread.name}, {thread.is_alive()}")
    # print("---")

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
        logger.debug("Print context flag detected, printing context")
        voice_control.print_context()
        
    voice_control.start()

    try:
        logger.debug("Entering main loop to monitor controller errors")
        while True:
            # controller_error_code = control_interface.hexapod.controller.get_error()
            # if controller_error_code != 0:
            #     print(f"Controller error: {controller_error_code}")
            #     voice_control.pause()
            #     time.sleep(1)
            #     control_interface.lights_handler.set_single_color(ColorRGB.RED)
            #     control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            #     break
            # for thread in threading.enumerate():
            #     logger.user_info(f"{thread.name}, {thread.is_alive()}")
            # print("---")
            time.sleep(1)
    except KeyboardInterrupt:
        logger.critical("KeyboardInterrupt detected, initiating shutdown")
        sys.stdout.write('\b' * 2)
        logger.critical('Stopping all tasks and deactivating hexapod due to keyboard interrupt...')
        control_interface.stop_control_task()
        voice_control.stop()
        voice_control.join()
        control_interface.lights_handler.off()
        logger.debug("Shutdown tasks completed")
    finally:
        time.sleep(1)
        control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
        control_interface.hexapod.deactivate_all_servos()
        # control_interface.hexapod.controller.close()
        logger.user_info('Exiting...')

if __name__ == '__main__':
    main()