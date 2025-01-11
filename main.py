import argparse
import sys
import time
import logging.config
import pathlib
import json
import atexit
import threading

from src.kws import VoiceControl
from src.control import ControlInterface
from src.lights import ColorRGB
from src.robot import PredefinedAnglePosition, PredefinedPosition
from pathlib import Path
from src.utils import logger

logger = logging.getLogger("main_logger")
logger2 = logging.getLogger("control_logger")

def setup_logging() -> None:
    logs_dir = pathlib.Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created missing logs directory at {logs_dir}")

    config_file = logs_dir / "config.json"
    
    if config_file.is_file():
        logger.debug(f"Loading logging configuration from {config_file}")
        with open(config_file, "rt") as f:
            logging.config.dictConfig(json.load(f))
        queue_handler = logging.getHandlerByName("queue_handler")
        if queue_handler is not None:
            logger.debug("Starting queue handler listener...")
            queue_handler.listener.start()
            queue_handler.listener._thread.name = "QueueHandlerListener"
            atexit.register(queue_handler.listener.stop)
    else:
        logging.basicConfig(level=logging.INFO)
        logger.warning(f"Logging configuration file not found at {config_file}")
        logger.debug("Using basic logging configuration")

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hexapod Robot Controller")
    parser.add_argument("--access_key", type=str, required=True, help="Picovoice Access Key")
    parser.add_argument("--audio_device_index", type=int, default=-1, help="Audio device index")
    parser.add_argument('--print_context', action='store_true', help='Print the context information.')
    parser.add_argument('--clean', '-c', action='store_true', help='Clean all logs in the logs directory.')
    args = parser.parse_args()
    logger.debug(f"Arguments parsed: {args}")
    return args

def clean_logs() -> None:
    logger.debug("Cleaning log files")
    logs_dir = pathlib.Path("logs")
    if logs_dir.is_dir():
        for log_file in logs_dir.glob("*.log"):
            log_file.unlink()
            logger.debug(f"Deleted log file: {log_file}")
        for log_file in logs_dir.glob("*.log.jsonl"):
            log_file.unlink()
            logger.debug(f"Deleted log file: {log_file}")
        logger.info("All log files have been cleaned.")
    else:
        logger.warning(f"Logs directory not found at {logs_dir}")

def main() -> None:
    logger.warning("Application started")
    args = parse_arguments()

    if args.clean:
        logger.debug("Clean flag detected, initiating log cleaning")
        clean_logs()

    setup_logging()

    # for thread in threading.enumerate():
    #     logger.info(f"{thread.name}, {thread.is_alive()}")

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
        
    voice_control.start()  # Start VoiceControl as a separate thread
    logger.debug("VoiceControl thread started")

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
            time.sleep(1)
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt detected, initiating shutdown")
        sys.stdout.write('\b' * 2)
        print("  ", flush=True)
        print('Stopping all tasks and deactivating hexapod due to keyboard interrupt...')
        control_interface.stop_control_task()
        voice_control.stop()
        voice_control.join()
        control_interface.lights_handler.off()
        logger.info("Shutdown tasks completed")
    finally:
        logger.info("Finalizing shutdown sequence")
        time.sleep(5)
        control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
        control_interface.hexapod.deactivate_all_servos()
        # control_interface.hexapod.controller.close()
        print('Exiting...')

if __name__ == '__main__':
    main()