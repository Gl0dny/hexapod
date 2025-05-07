from __future__ import annotations
from typing import TYPE_CHECKING
import logging.config
import os
import sys
import argparse
import sys
import time
import atexit
import threading
from pathlib import Path

import yaml

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if src_path not in sys.path:
    sys.path.append(src_path)

from kws import VoiceControl
from control import ControlInterface
from lights import ColorRGB
from robot import PredefinedAnglePosition, PredefinedPosition
from utils import rename_thread

if TYPE_CHECKING:
    from typing import Optional

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
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Voice Control for Hexapod')
    
    # Required arguments
    parser.add_argument('--access-key', type=str, required=True,
                        help='Picovoice Access Key for authentication')
    
    # Optional arguments
    parser.add_argument('--audio-device-index', type=int, default=-1,
                        help='Index of the audio input device (default: autoselect)')
    parser.add_argument('--log-dir', type=Path, default=Path('logs'),
                        help='Directory to store logs')
    parser.add_argument('--log-config-file', type=Path, default=Path('logs/config.yaml'),
                        help='Path to log configuration file')
    parser.add_argument('--clean', '-c', action='store_true',
                        help='Clean all logs in the logs directory.')
    parser.add_argument('--print-context', action='store_true',
                        help='Print context information.')
    
    # ODAS arguments
    parser.add_argument('--use-odas', action='store_true',
                        help='Use ODAS for audio input')
    parser.add_argument('--odas-dir', type=Path, default=Path('/home/hexapod/hexapod/'),
                        help='Directory where ODAS creates raw files')
    
    return parser.parse_args()

def clean_logs() -> None:
    project_dir = Path(__file__).parent
    log_patterns = ['*.log', '*.log.jsonl']
    for pattern in log_patterns:
        for log_file in project_dir.rglob(pattern):
            log_file.unlink()

def main() -> None:
    """Main entry point."""
    args = parse_arguments()
    
    # Clean logs if requested
    if args.clean:
        clean_logs()
    
    # Set up logging
    setup_logging(log_dir=args.log_dir, config_file=args.log_config_file)
    
    logger.user_info("Hexapod application started")
    
    # Initialize control interface
    control_interface = ControlInterface()
    
    control_interface.lights_handler.set_single_color(ColorRGB.RED)
    control_interface.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
    
    keyword_path = Path('src/kws/porcupine/hexapod_en_raspberry-pi_v3_0_0.ppn')
    context_path = Path('src/kws/rhino/hexapod_en_raspberry-pi_v3_0_0.rhn')
    
    # Initialize voice control
    voice_control = VoiceControl(
        keyword_path=keyword_path,
        context_path=context_path,
        access_key=args.access_key,
        control_interface=control_interface,
        device_index=args.audio_device_index,
        use_odas=args.use_odas,
        odas_dir=args.odas_dir
    )
    
    # Print context and exit if requested
    if args.print_context:
        logger.debug("Print context flag detected, printing context")
        voice_control.print_context()
        
    # Start voice control
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
            time.sleep(1)
    except KeyboardInterrupt:
        logger.critical("KeyboardInterrupt detected, initiating shutdown")
        sys.stdout.write('\b' * 2)
        logger.critical('Stopping all tasks and deactivating hexapod due to keyboard interrupt...')
        
        for thread in threading.enumerate():
            logger.user_info(f"{thread.name}, {thread.is_alive()}")
        print("---")
        
        voice_control.stop()
        voice_control.join()
        control_interface.stop_control_task()
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