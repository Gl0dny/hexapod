#!/usr/bin/env python3

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
from task_interface import TaskInterface
from robot import PredefinedPosition
from interface import setup_logging, clean_logs
from interface import GamepadHexapodController

if TYPE_CHECKING:
    from typing import Optional

logger = logging.getLogger("main_logger")

# Global shutdown event
shutdown_event = threading.Event()

def shutdown_callback():
    """Callback function to trigger program shutdown."""
    shutdown_event.set()

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
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    parser.add_argument('--clean', '-c', action='store_true',
                        help='Clean all logs in the logs directory.')
    parser.add_argument('--print-context', action='store_true',
                        help='Print context information.')
    

    
    return parser.parse_args()

def handle_button_interactions(task_interface, voice_control):
    """Handle button interactions for voice control mode."""
    action, is_running = task_interface.button_handler.check_button()
    
    if action == 'long_press':
        logger.user_info("Long press detected, starting sound source localization...")
        task_interface.sound_source_localization()
    elif action == 'toggle':
        if is_running:
            logger.user_info("Starting system...")
            task_interface.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            voice_control.unpause()
        else:
            logger.user_info("Stopping system...")
            voice_control.pause()
            task_interface.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            time.sleep(0.5)
            task_interface.hexapod.deactivate_all_servos()

def shutdown_cleanup(voice_control, manual_controller, task_interface):
    """Perform cleanup when shutting down the program."""
    logger.critical('Stopping all tasks and deactivating hexapod...')
    
    if voice_control:
        voice_control.stop()
        voice_control.join()
    if manual_controller:
        manual_controller.stop()
        manual_controller.join()
    if task_interface:
        task_interface.cleanup()
    logger.user_info('Exiting...')

    for thread in threading.enumerate():
        logger.user_info(f"{thread.name}, {thread.is_alive()}")
    print("---")

def initialize_application(args) -> TaskInterface:
    """Initialize the application and return the task interface."""
    # Clean logs if requested
    if args.clean:
        clean_logs()
    
    # Set up logging
    setup_logging(log_dir=args.log_dir, config_file=args.log_config_file, log_level=args.log_level)
    
    logger.user_info("Hexapod application started")
    logger.info(f"Logging level set to: {args.log_level}")

    # Initialize control interface
    task_interface = TaskInterface()
    return task_interface

def initialize_voice_control(args, task_interface) -> VoiceControl:
    """Initialize voice control and return the voice control instance."""
    keyword_path = Path('src/kws/porcupine/hexapod_en_raspberry-pi_v3_0_0.ppn')
    context_path = Path('src/kws/rhino/hexapod_en_raspberry-pi_v3_0_0.rhn')
    
    # Initialize voice control
    voice_control = VoiceControl(
        keyword_path=keyword_path,
        context_path=context_path,
        access_key=args.access_key,
        task_interface=task_interface,
        device_index=args.audio_device_index
    )
    
    # Print context
    if args.print_context:
        logger.debug("Print context flag detected, printing context")
        voice_control.print_context()

    voice_control.start()
    return voice_control

def initialize_manual_controller(task_interface, voice_control) -> Optional[GamepadHexapodController]:
    """Initialize manual controller and return it, or None if failed."""
    try:
        manual_controller = GamepadHexapodController(
            task_interface=task_interface,
            voice_control=voice_control,
            shutdown_callback=shutdown_callback
        )
        manual_controller.start()
        # Ensure voice control is paused in manual mode
        voice_control.pause()
        logger.user_info("Manual controller started successfully")
        return manual_controller
    except Exception as e:
        logger.warning(f"Failed to initialize manual controller: {e}")
        logger.user_info("Falling back to voice control mode")
        if not voice_control.pause_event.is_set():
            voice_control.unpause()  # Unpause voice control for fallback mode
        return None

def run_main_loop(voice_control, manual_controller, task_interface) -> None:
    """Run the main application loop."""
    cleanup_done = False
    
    try:
        while True:
            # Check for shutdown event (triggered by PS5 button)
            if shutdown_event.is_set():
                logger.critical("Shutdown event detected, initiating shutdown")
                shutdown_cleanup(voice_control, manual_controller, task_interface)
                cleanup_done = True
                break
                
            # controller_error_code = task_interface.hexapod.controller.get_error()
            # if controller_error_code != 0:
            #     print(f"Controller error: {controller_error_code}")
            #     voice_control.pause()
            #     time.sleep(1)
            #     task_interface.lights_handler.set_single_color(ColorRGB.RED)
            #     task_interface.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            #     break
            # time.sleep(1)
            
            if manual_controller:
                # Manual control mode - check if in voice control mode
                if manual_controller.current_mode == manual_controller.VOICE_CONTROL_MODE:
                    # Manual controller is in voice control mode - handle button interactions
                    handle_button_interactions(task_interface, voice_control)
                else:
                    # Manual controller is in body/gait control mode - just monitor for shutdown
                    # The manual controller runs independently, we just need to keep the main thread alive
                    pass
            else:
                # No manual controller - voice control mode only - handle button interactions
                handle_button_interactions(task_interface, voice_control)
            
            time.sleep(0.1)  # Small delay to prevent CPU overuse
            
    except KeyboardInterrupt:
        logger.critical("KeyboardInterrupt detected, initiating shutdown")
        sys.stdout.write('\b' * 2)
        shutdown_cleanup(voice_control, manual_controller, task_interface)
        cleanup_done = True
    finally:
        if not cleanup_done:
            shutdown_cleanup(voice_control, manual_controller, task_interface)

def main() -> None:
    """Main entry point."""
    args = parse_arguments()
    
    # Initialize application components
    task_interface = initialize_application(args)
    voice_control = initialize_voice_control(args, task_interface)
    manual_controller = initialize_manual_controller(task_interface, voice_control)
    
    # Run main loop
    run_main_loop(voice_control, manual_controller, task_interface)

if __name__ == '__main__':
    main()