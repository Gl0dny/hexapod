from __future__ import annotations
from typing import TYPE_CHECKING
import logging.config
import sys
import argparse
import time
import threading
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from kws import VoiceControl
from control import ControlInterface
from lights import ColorRGB
from robot import PredefinedAnglePosition, PredefinedPosition
from interface import setup_logging, clean_logs

if TYPE_CHECKING:
    from typing import Optional

logger = logging.getLogger("main_logger")

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
    parser.add_argument('--log-config-file', type=Path, default=Path('src/interface/logging/config/config.yaml'),
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

    control_interface.hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        
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
    
    # Print context
    if args.print_context:
        logger.debug("Print context flag detected, printing context")
        voice_control.print_context()
    
    # Start voice control
    voice_control.start()
    
    try:
        # logger.debug("Entering main loop to monitor controller errors")
        logger.debug("Waiting for button press to start the system")
        while True:
            # controller_error_code = control_interface.hexapod.controller.get_error()
            # if controller_error_code != 0:
            #     print(f"Controller error: {controller_error_code}")
            #     voice_control.pause()
            #     time.sleep(1)
            #     control_interface.lights_handler.set_single_color(ColorRGB.RED)
            #     control_interface.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            #     break
            # time.sleep(1)
            action, is_running = control_interface.button_handler.check_button()
            
            if action == 'long_press':
                logger.user_info("Long press detected, starting sound source localization...")
                control_interface.sound_source_localization()
            elif action == 'toggle':
                if is_running:
                    logger.user_info("Starting system...")
                    control_interface.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
                    voice_control.unpause()
                else:
                    logger.user_info("Stopping system...")
                    voice_control.pause()
                    control_interface.lights_handler.off()
                    control_interface.hexapod.deactivate_all_servos()
            
            time.sleep(0.1)  # Small delay to prevent CPU overuse
            
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
        control_interface.hexapod.deactivate_all_servos()
        control_interface.button_handler.cleanup()
        logger.user_info('Exiting...')

if __name__ == '__main__':
    main()