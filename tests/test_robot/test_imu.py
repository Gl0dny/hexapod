import time
import sys
import os
import argparse
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent.parent / 'src')
sys.path.append(src_path)

from robot import Hexapod

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test IMU readings for different orientations')
    parser.add_argument('--duration', type=float, default=5.0,
                      help='Duration of each test in seconds (default: 5.0)')
    args = parser.parse_args()
    
    hexapod = None
    
    try:
        print("Initializing Hexapod...")
        hexapod = Hexapod()
        
        print("\nFirst, let's identify the IMU orientation...")
        print("Please move the robot in different directions and observe the values:")
        print("\nAccelerometer (Accel):")
        print("1. When you tilt forward, the X acceleration should become negative")
        print("2. When you tilt backward, the X acceleration should become positive")
        print("3. When you tilt left, the Y acceleration should become negative")
        print("4. When you tilt right, the Y acceleration should become positive")
        print("5. The Z acceleration should be close to 1.0 when flat")
        
        print("\nGyroscope (Gyro) - measures rotation speed in degrees per second:")
        print("X: Pitch rate (forward/backward rotation)")
        print("Y: Roll rate (left/right rotation)")
        print("Z: Yaw rate (clockwise/counterclockwise rotation)")
        print("\nPress Enter to start orientation test...")
        input()
        
        print("\nMove the robot in different directions to identify orientation")
        print("Press Ctrl+C when you're ready to proceed with the main test")
        print("Format: Accel: X=±X.XX Y=±Y.XX Z=±Z.XX | Gyro: X=±X.XX Y=±Y.XX Z=±Z.XX")
        
        try:
            while True:
                accel_x, accel_y, accel_z = hexapod.imu.get_acceleration()
                gyro_x, gyro_y, gyro_z = hexapod.imu.get_gyroscope()
                print(f"\rAccel: X={accel_x:+.2f} Y={accel_y:+.2f} Z={accel_z:+.2f} | "
                      f"Gyro: X={gyro_x:+.2f} Y={gyro_y:+.2f} Z={gyro_z:+.2f}", end="")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nOrientation test completed. Now proceeding with main test...")
        
        print(f"\nIMU Test Instructions (each test will last {args.duration} seconds):")
        print("1. Keep the robot on a flat surface")
        print("2. Tilt the robot forward (pitch)")
        print("3. Tilt the robot backward (pitch)")
        print("4. Tilt the robot left (roll)")
        print("5. Tilt the robot right (roll)")
        print("6. Press Ctrl+C to stop")
        
        print("\nStarting main IMU test...")
        print("Press Enter to start...")
        input()
        
        # Test flat surface
        print("\nTesting flat surface...")
        start_time = time.time()
        while time.time() - start_time < args.duration:
            accel_x, accel_y, accel_z = hexapod.imu.get_acceleration()
            gyro_x, gyro_y, gyro_z = hexapod.imu.get_gyroscope()
            print(f"\rAccel: X={accel_x:+.2f} Y={accel_y:+.2f} Z={accel_z:+.2f} | "
                  f"Gyro: X={gyro_x:+.2f} Y={gyro_y:+.2f} Z={gyro_z:+.2f}", end="")
            time.sleep(0.1)
        
        # Test forward tilt (pitch)
        print("\n\nTilt the robot forward...")
        start_time = time.time()
        while time.time() - start_time < args.duration:
            accel_x, accel_y, accel_z = hexapod.imu.get_acceleration()
            gyro_x, gyro_y, gyro_z = hexapod.imu.get_gyroscope()
            print(f"\rAccel: X={accel_x:+.2f} Y={accel_y:+.2f} Z={accel_z:+.2f} | "
                  f"Gyro: X={gyro_x:+.2f} Y={gyro_y:+.2f} Z={gyro_z:+.2f}", end="")
            time.sleep(0.1)
        
        # Test backward tilt (pitch)
        print("\n\nTilt the robot backward...")
        start_time = time.time()
        while time.time() - start_time < args.duration:
            accel_x, accel_y, accel_z = hexapod.imu.get_acceleration()
            gyro_x, gyro_y, gyro_z = hexapod.imu.get_gyroscope()
            print(f"\rAccel: X={accel_x:+.2f} Y={accel_y:+.2f} Z={accel_z:+.2f} | "
                  f"Gyro: X={gyro_x:+.2f} Y={gyro_y:+.2f} Z={gyro_z:+.2f}", end="")
            time.sleep(0.1)
        
        # Test left tilt (roll)
        print("\n\nTilt the robot left...")
        start_time = time.time()
        while time.time() - start_time < args.duration:
            accel_x, accel_y, accel_z = hexapod.imu.get_acceleration()
            gyro_x, gyro_y, gyro_z = hexapod.imu.get_gyroscope()
            print(f"\rAccel: X={accel_x:+.2f} Y={accel_y:+.2f} Z={accel_z:+.2f} | "
                  f"Gyro: X={gyro_x:+.2f} Y={gyro_y:+.2f} Z={gyro_z:+.2f}", end="")
            time.sleep(0.1)
        
        # Test right tilt (roll)
        print("\n\nTilt the robot right...")
        start_time = time.time()
        while time.time() - start_time < args.duration:
            accel_x, accel_y, accel_z = hexapod.imu.get_acceleration()
            gyro_x, gyro_y, gyro_z = hexapod.imu.get_gyroscope()
            print(f"\rAccel: X={accel_x:+.2f} Y={accel_y:+.2f} Z={accel_z:+.2f} | "
                  f"Gyro: X={gyro_x:+.2f} Y={gyro_y:+.2f} Z={gyro_z:+.2f}", end="")
            time.sleep(0.1)
            
        # Additional gyroscope tests
        print("\n\nNow let's test the gyroscope specifically:")
        print("1. Rotate the robot forward and backward (watch Gyro X)")
        print("2. Rotate the robot left and right (watch Gyro Y)")
        print("3. Rotate the robot clockwise/counterclockwise (watch Gyro Z)")
        print("Press Enter to start gyroscope test...")
        input()
        
        print("\nMove the robot in different rotations to observe gyroscope values")
        print("Press Ctrl+C when you're done")
        try:
            while True:
                accel_x, accel_y, accel_z = hexapod.imu.get_acceleration()
                gyro_x, gyro_y, gyro_z = hexapod.imu.get_gyroscope()
                print(f"\rAccel: X={accel_x:+.2f} Y={accel_y:+.2f} Z={accel_z:+.2f} | "
                      f"Gyro: X={gyro_x:+.2f} Y={gyro_y:+.2f} Z={gyro_z:+.2f}", end="")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nGyroscope test completed.")
            
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
    except Exception as e:
        print(f"\n\nError during test: {e}")
    finally:
        if hexapod:
            print("\nDeactivating all servos...")
            try:
                hexapod.deactivate_all_servos()
            except Exception as e:
                print(f"Error deactivating servos: {e}")
        
        print("Test completed.")

if __name__ == "__main__":
    main() 