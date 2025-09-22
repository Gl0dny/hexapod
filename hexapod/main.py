#!/usr/bin/env python3

from __future__ import annotations
from typing import TYPE_CHECKING
import argparse
import logging.config
import sys
import time
import threading
from pathlib import Path

from hexapod.config import Config, create_config_parser
from hexapod.kws import VoiceControl
from hexapod.task_interface import TaskInterface
from hexapod.robot import PredefinedPosition
from hexapod.interface import setup_logging, clean_logs, get_custom_logger
from hexapod.interface import GamepadHexapodController

if TYPE_CHECKING:
    from typing import Optional

logger = get_custom_logger("main_logger")

# Global shutdown event
shutdown_event = threading.Event()


def shutdown_callback() -> None:
    """
    Callback function to trigger program shutdown.

    Sets the global shutdown event to signal all threads to stop gracefully.
    This function is typically called by signal handlers or other shutdown mechanisms.
    """
    shutdown_event.set()


def handle_button_interactions(task_interface: TaskInterface) -> None:
    """
    Handle button interactions for voice control mode.

    Processes different button press actions:
    - Long press: Starts sound source localization
    - Short press (toggle): Starts/stops the system
    - Short press (stop_task): Stops current blocking task

    Args:
        task_interface (TaskInterface): The task interface managing robot operations
    """
    action, is_running = task_interface.button_handler.check_button()

    if action == "long_press":
        logger.user_info("Long press detected, starting sound source localization...")
        task_interface.sound_source_localization()
    elif action == "toggle":
        if is_running:
            logger.user_info("Starting system...")
            task_interface.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            task_interface.request_unpause_voice_control()
        else:
            logger.user_info("Stopping system...")
            task_interface.request_pause_voice_control()
            task_interface.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            time.sleep(0.5)
            task_interface.hexapod.deactivate_all_servos()
    elif action == "stop_task":
        logger.user_info(
            "Button pressed during blocking task, stopping current task..."
        )
        task_interface.stop_task()
        # Unpause external control and voice control after stopping the task
        task_interface.request_unblock_voice_control_pausing()
        task_interface.request_unpause_voice_control()


def shutdown_cleanup(
    voice_control: Optional[VoiceControl],
    manual_controller: Optional[GamepadHexapodController],
    task_interface: TaskInterface,
) -> None:
    """
    Perform cleanup when shutting down the program.

    Stops all running threads and performs necessary cleanup operations:
    - Stops and joins voice control thread
    - Stops and joins manual controller thread
    - Cleans up task interface resources
    - Logs thread status for debugging

    Args:
        voice_control (Optional[VoiceControl]): Voice control instance to stop
        manual_controller (Optional[GamepadHexapodController]): Manual controller to stop
        task_interface (TaskInterface): Task interface to clean up
    """
    logger.critical("Stopping all tasks and deactivating hexapod...")

    if voice_control:
        voice_control.stop()
        voice_control.join()
        logger.debug("VoiceControl thread joined")
    if manual_controller:
        manual_controller.stop()
        manual_controller.join()
        logger.debug("Manual controller thread joined")
    if task_interface:
        task_interface.cleanup()
    logger.user_info("Exiting...")

    for thread in threading.enumerate():
        logger.debug(f"{thread.name}, {thread.is_alive()}")
    print("---")


def create_main_parser() -> argparse.ArgumentParser:
    """
    Create the main argument parser for the hexapod application.

    Sets up command line argument parsing with options for:
    - Picovoice configuration (access key)
    - Logging configuration (level, clean logs)
    - Manual controller settings
    - Audio device selection

    Returns:
        argparse.ArgumentParser: Configured argument parser with all application options
    """
    parser = argparse.ArgumentParser(
        description="Hexapod Voice Control System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  hexapod --access-key "YOUR_PICOVOICE_KEY" --log-level INFO --clean
        """,
    )

    # Add Picovoice configuration arguments
    picovoice_parser = create_config_parser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path.home() / ".config" / "hexapod" / ".picovoice.env",
        help="Path to .env configuration file (default: ~/.config/hexapod/.picovoice.env)",
    )
    parser._add_action(picovoice_parser._actions[1])  # --access-key

    # Logging arguments
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("logs"),
        help="Directory to store logs (default: logs)",
    )
    # Get the package directory for absolute paths
    package_dir = Path(__file__).resolve().parent
    parser.add_argument(
        "--log-config-file",
        type=Path,
        default=package_dir / "interface" / "logging" / "config" / "config.yaml",
        help="Path to log configuration file",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=[
            "DEBUG",
            "INFO",
            "USER_INFO",
            "ODAS_USER_INFO",
            "GAMEPAD_MODE_INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ],
        help="Logging level: DEBUG (verbose), INFO (standard), USER_INFO (user messages), ODAS_USER_INFO (audio processing), GAMEPAD_MODE_INFO (controller), WARNING, ERROR, CRITICAL (default: INFO)",
    )

    # Utility arguments
    parser.add_argument(
        "--clean",
        "-c",
        action="store_true",
        help="Clean all logs in the logs directory.",
    )
    parser.add_argument(
        "--print-context", action="store_true", help="Print context information."
    )

    return parser


def create_application_components(
    config: Config, args: argparse.Namespace
) -> tuple[TaskInterface, VoiceControl]:
    """
    Factory function to create all application components with proper dependencies.

    This function ensures that all components are properly initialized and their
    dependencies are correctly injected, eliminating the need for manual assignment.

    Args:
        config (Config): Configuration instance with validated settings
        args (argparse.Namespace): Parsed command line arguments

    Returns:
        tuple[TaskInterface, VoiceControl]: Tuple containing:
            - TaskInterface: Main task management interface
            - VoiceControl: Voice control system instance

    Raises:
        ValueError: If required configuration values are missing
        FileNotFoundError: If required files are not found
    """
    if args.clean:
        clean_logs()

    setup_logging(
        log_dir=args.log_dir, config_file=args.log_config_file, log_level=args.log_level
    )

    logger.user_info("Hexapod application started")
    logger.info(f"Logging level set to: {args.log_level}")

    task_interface = TaskInterface()

    # Get paths relative to the package
    package_dir = Path(__file__).resolve().parent
    keyword_path = (
        package_dir / "kws" / "porcupine" / "hexapod_en_raspberry-pi_v3_0_0.ppn"
    )
    context_path = package_dir / "kws" / "rhino" / "hexapod_en_raspberry-pi_v3_0_0.rhn"

    voice_control = VoiceControl(
        keyword_path=keyword_path,
        context_path=context_path,
        access_key=config.get_picovoice_key(),
        task_interface=task_interface,
        device_index=-1,  # Auto-detect ReSpeaker 6
    )

    task_interface.set_voice_control(voice_control)
    task_interface.wake_up()

    if args.print_context:
        logger.debug("Print context flag detected, printing context")
        voice_control.print_context_info()

    logger.info("Application components created successfully with proper dependencies")
    return task_interface, voice_control


def initialize_manual_controller(
    task_interface: TaskInterface,
    voice_control: VoiceControl,
    config: Config,
    args: argparse.Namespace,
) -> Optional[GamepadHexapodController]:
    """
    Initialize manual controller and return it, or None if failed.

    Attempts to create and start a gamepad controller for manual robot control.
    If initialization fails, falls back to voice control mode.

    Args:
        task_interface (TaskInterface): Task interface for robot control
        voice_control (VoiceControl): Voice control instance to pause/unpause
        config (Config): Configuration instance (unused but kept for consistency)
        args (argparse.Namespace): Command line arguments (unused but kept for consistency)

    Returns:
        Optional[GamepadHexapodController]: Initialized controller or None if failed
    """

    try:
        # Ensure voice control is paused in manual mode
        task_interface.request_pause_voice_control()
        manual_controller = GamepadHexapodController(
            task_interface=task_interface,
            voice_control=voice_control,
            shutdown_callback=shutdown_callback,
        )
        manual_controller.start()
        logger.user_info("Manual controller started successfully")
        return manual_controller
    except Exception as e:
        logger.warning(f"Failed to initialize manual controller: {e}")
        logger.user_info("Falling back to voice control mode")
        task_interface.request_unpause_voice_control()  # Unpause voice control for fallback mode
        return None


def run_main_loop(
    voice_control: Optional[VoiceControl],
    manual_controller: Optional[GamepadHexapodController],
    task_interface: TaskInterface,
) -> None:
    """
    Run the main application loop.

    Continuously monitors for shutdown events and handles button interactions.
    The loop runs until a shutdown event is triggered, then performs cleanup.

    Args:
        voice_control (Optional[VoiceControl]): Voice control instance (may be None)
        manual_controller (Optional[GamepadHexapodController]): Manual controller (may be None)
        task_interface (TaskInterface): Task interface for robot operations
    """
    cleanup_done = False

    try:
        while True:
            # Check for shutdown event (triggered by PS5 button)
            if shutdown_event.is_set():
                logger.critical("Shutdown event detected, initiating shutdown")
                shutdown_cleanup(voice_control, manual_controller, task_interface)
                cleanup_done = True
                break

            if manual_controller:
                # Manual control mode - check if in voice control mode
                if (
                    manual_controller.current_mode
                    == manual_controller.VOICE_CONTROL_MODE
                ):
                    # Manual controller is in voice control mode - handle button interactions
                    handle_button_interactions(task_interface)
                else:
                    # Manual controller is in body/gait control mode - just monitor for shutdown
                    # The manual controller runs independently, just need to keep the main thread alive
                    pass
            else:
                # No manual controller - voice control mode only - handle button interactions
                handle_button_interactions(task_interface)

            time.sleep(0.1)  # Small delay to prevent CPU overuse

    except KeyboardInterrupt:
        logger.critical("KeyboardInterrupt detected, initiating shutdown")
        sys.stdout.write("\b" * 2)
        shutdown_cleanup(voice_control, manual_controller, task_interface)
        cleanup_done = True
    finally:
        if not cleanup_done:
            shutdown_cleanup(voice_control, manual_controller, task_interface)


def main() -> None:  # pragma: no cover
    """
    Main entry point for the Hexapod Voice Control System.

    Initializes the application, validates configuration, creates components,
    and starts the main control loop. Handles both voice control and manual
    control modes with proper error handling and cleanup.

    Raises:
        SystemExit: If configuration validation fails
        KeyboardInterrupt: If user interrupts the program
    """
    parser = create_main_parser()
    args = parser.parse_args()

    # Create configuration object for environment settings
    config = Config(config_file=args.config)
    config.update_from_args(args)

    # Validate environment settings
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nFor help with configuration, run: hexapod --help")
        print("For installation and setup instructions, see: INSTALL.md")
        sys.exit(1)

    # Create all application components with proper dependencies using factory
    task_interface, voice_control = create_application_components(config, args)

    # Start voice control
    voice_control.start()

    # Initialize manual controller
    manual_controller = initialize_manual_controller(
        task_interface, voice_control, config, args
    )

    # Run main loop
    run_main_loop(voice_control, manual_controller, task_interface)


if __name__ == "__main__":
    main()
