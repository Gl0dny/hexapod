import argparse
import os
import asyncio
from src.kws import VoiceControl
from src.control.control_module import ControlModule
from src.control.state_manager import StateManager
from src.hexapod.hexapod import Hexapod
from src.control.gait_generator import GaitGenerator

async def main():
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

    keyword_path = os.path.join(os.path.dirname(__file__), 'src/kws/porcupine/hexapod_en_raspberry-pi_v3_0_0.ppn')
    context_path = os.path.join(os.path.dirname(__file__), 'src/kws/rhino/hexapod_en_raspberry-pi_v3_0_0.rhn')

    hexapod = Hexapod()
    gait_generator = GaitGenerator(hexapod)
    control = ControlModule(gait_generator)
    state_manager = StateManager()

    voice_control = VoiceControl(
        keyword_path=keyword_path,
        context_path=context_path,
        access_key=args.access_key,
        device_index=args.audio_device_index,
        control_module=control,
        state_manager=state_manager
    )
    
    if args.print_context:
        voice_control.print_context()
    
    # asyncio.run(voice_control.run())
    await voice_control.run()

if __name__ == '__main__':
    asyncio.run(main())

# Explanation of Components
# Argument Parsing:

# --access_key: Required argument for authentication with Picovoice services.
# --audio_device_index: Specifies the audio input device.
# --print_context: Optional flag to print context information for debugging.
# Path Definitions:

# keyword_path: Path to the keyword file for wake word detection.
# context_path: Path to the context file for intent recognition.
# Initialization Sequence:

# Hexapod: Initializes the hexapod robot's hardware control.
# GaitGenerator: Manages gait patterns and sequences using the hexapod instance.
# ControlModule: Handles high-level control commands and interfaces with the gait generator.
# StateManager: Manages the state of the robot (e.g., moving, idle).
# VoiceControl: Integrates voice commands with the control module and manages intent dispatching.
# Running the Voice Control:

# The VoiceControl instance is run within an asyncio event loop, allowing for asynchronous handling of voice commands and movements.
# Additional Recommendations
# Main Program Loop:

# The asyncio.run(voice_control.run()) starts the asynchronous loop that listens for voice commands and processes them accordingly.
# Ensure that all asynchronous tasks within your classes (Hexapod, GaitGenerator, etc.) are properly awaited to prevent blocking operations.
# Error Handling:

# Implement try-except blocks as needed to handle exceptions and ensure that the hexapod can recover gracefully from errors.
# Shutdown Procedures:

# Ensure that your program can handle graceful shutdowns, closing serial connections and stopping asynchronous tasks properly.
# Logging:

# Utilize the existing logging setup to monitor the hexapod's operations and debug issues effectively.
# File References
# hexapod.py: Contains the Hexapod class responsible for initializing and controlling the hexapod robot.
# gait_generator.py: Contains the GaitGenerator class that defines and manages gait patterns.
# control_module.py: Contains the ControlModule class for high-level control commands.
# state_manager.py: Contains the StateManager class for managing the robot's state.
# voice_control.py: Contains the VoiceControl class that integrates voice commands with the control modules.
# By structuring your main.py as shown above, you establish a clear entry point for your hexapod's software, ensuring that all components are properly initialized and integrated into the main program loop.



# explain how this asyncio works , why this error occurred and how exactly your changes fix it

# GitHub Copilot
# The error and the use of asyncio can be understood as follows:

# How asyncio Works
# Event Loop: asyncio operates around an event loop that manages and dispatches asynchronous tasks.
# Coroutines: Functions defined with async def can perform non-blocking operations using await.
# Tasks: asyncio.create_task schedules coroutines to run concurrently within the event loop.
# Why the Error Occurred
# No Running Event Loop: The error RuntimeError: no running event loop occurs because asyncio.create_task was called outside of an active event loop.
# Initialization Timing: In the original code, Hexapod() was instantiated before the event loop was started, leading to the coroutine not being awaited properly.
# How the Changes Fix It
# Asynchronous main Function: By defining main as an async function, all asynchronous operations are managed within the event loop.
# Using asyncio.run: Wrapping the call to main with asyncio.run(main()) ensures that an event loop is created and running when Hexapod and other asynchronous tasks are initialized.
# Proper Task Scheduling: This setup ensures that asyncio.create_task is called within the context of a running event loop, preventing the RuntimeError.
# These changes ensure that all asynchronous components are properly managed within the event loop, allowing coroutines to be awaited and tasks to be scheduled without errors.