import argparse
import os
import asyncio
from src.kws import VoiceControl
from src.control.control_module import ControlModule
from src.control.state_manager import StateManager
from src.hexapod.hexapod import Hexapod
from src.control.gait_generator import GaitGenerator

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
    
    asyncio.run(voice_control.run())

if __name__ == '__main__':
    main()