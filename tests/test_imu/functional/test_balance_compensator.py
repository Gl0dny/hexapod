import time
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent.parent / 'src')
sys.path.append(src_path)

from robot import Hexapod, PredefinedPosition
from robot import BalanceCompensator

def main():
    hexapod = None
    compensator = None
    
    try:
        print("Initializing Hexapod...")
        hexapod = Hexapod()
        
        print("Moving to home position...")
        hexapod.move_to_position(PredefinedPosition.ZERO)
        hexapod.wait_until_motion_complete()
        
        print("Creating BalanceCompensator...")
        compensator = BalanceCompensator(hexapod, compensation_factor=0.3)  # Reduced factor for safety
        
        print("Starting balance compensation...")
        print("The robot will now try to maintain its balance.")
        print("You can tilt the robot to see the compensation in action.")
        print("Press Ctrl+C to stop.")
        
        compensator.start()
        
        # Keep the main thread alive
        while True:
            try:
                # Print current IMU readings for monitoring
                accel_x, accel_y, accel_z = hexapod.imu.get_acceleration()
                gyro_x, gyro_y, gyro_z = hexapod.imu.get_gyroscope()
                
                print(f"\rAccel: X={accel_x:+.2f} Y={accel_y:+.2f} Z={accel_z:+.2f} | "
                      f"Gyro: X={gyro_x:+.2f} Y={gyro_y:+.2f} Z={gyro_z:+.2f}", end="")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                break
            
    except KeyboardInterrupt:
        print("\nReceived Ctrl+C, stopping...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print("Cleaning up...")
        if compensator:
            print("Stopping balance compensation...")
            compensator.stop()
        
        if hexapod:
            print("Moving to home position...")
            try:
                hexapod.move_to_position(PredefinedPosition.ZERO)
                hexapod.wait_until_motion_complete()
            except Exception as e:
                print(f"Error moving to home position: {e}")
            
            print("Deactivating all servos...")
            try:
                hexapod.deactivate_all_servos()
            except Exception as e:
                print(f"Error deactivating servos: {e}")
        
        print("Test completed.")

if __name__ == "__main__":
    main() 