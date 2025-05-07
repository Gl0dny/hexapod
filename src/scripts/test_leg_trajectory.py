#!/usr/bin/env python3
import sys
import time
import numpy as np
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from robot import Hexapod
from robot.gait_generator import BaseGait, GaitPhase

class TestGait(BaseGait):
    """Test gait for demonstrating different movement patterns."""
    def _setup_gait_graph(self) -> None:
        self.gait_graph[GaitPhase.TRIPOD_A] = [GaitPhase.TRIPOD_B]
        self.gait_graph[GaitPhase.TRIPOD_B] = [GaitPhase.TRIPOD_A]

    def get_state(self, phase: GaitPhase) -> None:
        pass  # Not needed for this test

    def get_swing_position(self, leg_index: int) -> tuple[float, float, float]:
        pos = (
            self.reference_position[0] + self.swing_distance,
            self.reference_position[1],
            self.reference_position[2] + self.swing_height
        )
        print(f"Calculated swing position: {pos}")
        return pos

    def get_stance_position(self, leg_index: int) -> tuple[float, float, float]:
        pos = (
            self.reference_position[0] - self.stance_distance,
            self.reference_position[1],
            self.reference_position[2]
        )
        print(f"Calculated stance position: {pos}")
        return pos

def test_linear_movement(hexapod: Hexapod, leg_index: int):
    """Test the old linear movement pattern."""
    print("\nTesting linear movement...")
    
    # Create test gait with linear movement
    gait = TestGait(hexapod, 
                   swing_distance=30.0,
                   swing_height=30.0,
                   stance_distance=30.0,
                   transition_steps=1)  # Force linear movement
    
    # Get start and end positions
    start_pos = gait.get_stance_position(leg_index)
    end_pos = gait.get_swing_position(leg_index)
    
    print(f"\nMoving leg {leg_index} from {start_pos} to {end_pos}")
    print(f"Reference position: {gait.reference_position}")
    print(f"Swing height: {gait.swing_height}")
    
    # Move to start position
    print(f"\nMoving to start position: {start_pos}")
    hexapod.move_leg(leg_index, start_pos[0], start_pos[1], start_pos[2])
    time.sleep(1)
    
    # Move to end position (linear)
    print(f"\nMoving to end position: {end_pos}")
    hexapod.move_leg(leg_index, end_pos[0], end_pos[1], end_pos[2])
    time.sleep(1)
    
    # Move back to start (linear)
    print(f"\nMoving back to start position: {start_pos}")
    hexapod.move_leg(leg_index, start_pos[0], start_pos[1], start_pos[2])
    time.sleep(1)

def test_curved_movement(hexapod: Hexapod, leg_index: int):
    """Test the new curved movement pattern."""
    print("\nTesting curved movement...")
    
    # Create test gait with curved movement
    gait = TestGait(hexapod,
                   swing_distance=30.0,
                   swing_height=30.0,
                   stance_distance=30.0,
                   transition_steps=10)  # Enable smooth transitions
    
    # Get start and end positions
    start_pos = gait.get_stance_position(leg_index)
    end_pos = gait.get_swing_position(leg_index)
    
    print(f"\nMoving leg {leg_index} from {start_pos} to {end_pos}")
    print(f"Reference position: {gait.reference_position}")
    print(f"Swing height: {gait.swing_height}")
    print(f"Number of transition steps: {gait.transition_steps}")
    
    # Move to start position
    print(f"\nMoving to start position: {start_pos}")
    hexapod.move_leg(leg_index, start_pos[0], start_pos[1], start_pos[2])
    time.sleep(1)
    
    # Execute curved movement
    print("\nExecuting curved swing movement:")
    for step in range(gait.transition_steps):
        progress = step / (gait.transition_steps - 1)
        current_pos = gait.calculate_swing_trajectory(start_pos, end_pos, progress)
        print(f"Step {step + 1}/{gait.transition_steps} - Progress: {progress:.2f} - Position: {current_pos}")
        hexapod.move_leg(leg_index, current_pos[0], current_pos[1], current_pos[2])
        time.sleep(0.02)  # 50Hz update rate
    
    time.sleep(1)
    
    # Move back to start with curved movement
    print("\nExecuting curved stance movement:")
    for step in range(gait.transition_steps):
        progress = step / (gait.transition_steps - 1)
        current_pos = gait.calculate_stance_trajectory(end_pos, start_pos, progress)
        print(f"Step {step + 1}/{gait.transition_steps} - Progress: {progress:.2f} - Position: {current_pos}")
        hexapod.move_leg(leg_index, current_pos[0], current_pos[1], current_pos[2])
        time.sleep(0.02)  # 50Hz update rate
    
    time.sleep(1)

def main():
    # Initialize hexapod
    hexapod = Hexapod()
    
    try:
        # Test leg index (0-5)
        test_leg = 0
        
        print("Starting leg movement tests...")
        print("Press Ctrl+C to stop")
        
        while True:
            # Test linear movement
            test_linear_movement(hexapod, test_leg)
            time.sleep(2)  # Pause between tests
            
            # Test curved movement
            test_curved_movement(hexapod, test_leg)
            time.sleep(2)  # Pause between tests
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    finally:
        # Cleanup
        hexapod.deactivate_all_servos()

if __name__ == "__main__":
    main() 