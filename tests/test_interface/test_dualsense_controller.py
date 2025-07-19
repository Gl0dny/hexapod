"""
Simple script to test PS5 controller detection and show available inputs.

This helps verify that your PS5 controller is properly connected and working.

Usage:
    python test_controller_detection.py
"""

import sys
import time
import os
import warnings
import subprocess

# Silence pygame warnings BEFORE importing pygame
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pygame")
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")
warnings.filterwarnings("ignore", message=".*pkg_resources.*")
warnings.filterwarnings("ignore", message=".*neon capable.*")
warnings.filterwarnings("ignore", message=".*pygame.*")

try:
    import pygame
except ImportError:
    print("pygame not available. Install with: pip install pygame")
    sys.exit(1)

def run_command_safely(command, timeout=5):
    """Run a command safely with timeout and error handling."""
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout} seconds", -1
    except FileNotFoundError:
        return "", f"Command not found: {command[0]}", -1
    except Exception as e:
        return "", f"Error running command: {e}", -1

def test_controller_functionality():
    """Test PS5 controller functionality and show available inputs."""
    
    print("\n\nPS5 Controller Detection Test")
    print("=" * 40)
    
    # Set display environment for headless systems
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    
    # Initialize pygame
    pygame.init()
    pygame.joystick.init()
    
    # Check for controllers
    joystick_count = pygame.joystick.get_count()
    print(f"Found {joystick_count} joystick(s)")
    
    if joystick_count == 0:
        print("No controllers detected!")
        print("\nTroubleshooting:")
        print("1. Make sure controller is connected via USB or paired via Bluetooth")
        print("2. For Bluetooth: Hold PS + Create buttons for 3 seconds to enter pairing mode")
        print("3. Check if controller appears in 'lsusb' or 'bluetoothctl devices'")
        return
    
    # Test each controller
    for i in range(joystick_count):
        print(f"\n--- Controller {i} ---")
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        
        name = joystick.get_name()
        print(f"Name: {name}")
        print(f"GUID: {joystick.get_guid()}")
        print(f"Axes: {joystick.get_numaxes()}")
        print(f"Buttons: {joystick.get_numbuttons()}")
        print(f"Hats: {joystick.get_numhats()}")
        
        # Show axis values
        print("\nAxes (move sticks/triggers to see values):")
        print("PS5 DualSense Controller Axis Layout:")
        print("  [0] Left X: -1 (left) to +1 (right)")
        print("  [1] Left Y: -1 (up) to +1 (down) - INVERTED")
        print("  [2] Right X: -1 (left) to +1 (right)")
        print("  [3] Right Y: -1 (up) to +1 (down) - INVERTED")
        print("  [4] L2: -1 (not pressed) to +1 (fully pressed)")
        print("  [5] R2: -1 (not pressed) to +1 (fully pressed)")
        print("Format: [Left X, Left Y, Right X, Right Y, L2, R2]")
        
        # Show button mapping
        print("\nButton mapping (press buttons to see):")
        print("PS5 DualSense Controller Button Layout:")
        print("  [0] X (Cross)")
        print("  [1] Circle")
        print("  [2] Square")
        print("  [3] Triangle")
        print("  [4] Create/Broadcast")
        print("  [5] PS5")
        print("  [6] Options")
        print("  [7] L3")
        print("  [8] R3")
        print("  [9] L1")
        print("  [10] R1")
        print("  [11] D-pad Up")
        print("  [12] D-pad Down")
        print("  [13] D-pad Left")
        print("  [14] D-pad Right")
        print("  [15] Mute")
        print("  [16] Touchpad")
        print("Format: [X, Circle, Square, Triangle, Create, PS5, Options, L3, R3, L1, R1, D-pad Up, D-pad Down, D-pad Left, D-pad Right, Mute, Touchpad]")
        
        
        # Real-time input monitoring
        print("\nPress Ctrl+C to stop monitoring...")
        print("Move sticks and press buttons to see live values:")
        
        try:
            while True:
                # Process events without display
                for event in pygame.event.get():
                    pass
                
                # Get axis values
                axes = [joystick.get_axis(j) for j in range(joystick.get_numaxes())]
                
                # Get button states
                buttons = [joystick.get_button(j) for j in range(joystick.get_numbuttons())]
                
                # Get hat values
                hats = [joystick.get_hat(j) for j in range(joystick.get_numhats())]
                
                # Display values
                print(f"\rAxes: {[f'{x:6.3f}' for x in axes]} | "
                      f"Buttons: {buttons} | "
                      f"Hats: {hats}", end="", flush=True)
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            break
    
    # Cleanup
    pygame.quit()
    print("\nTest completed!")

def check_system_controllers():
    """Check for controllers at system level."""
    print("\nSystem-level controller check:")
    print("=" * 40)
    
    # Check USB devices
    print("USB devices:")
    stdout, stderr, returncode = run_command_safely(['lsusb'], timeout=3)
    if returncode == 0:
        usb_devices = stdout
        found_controller = False
        for line in usb_devices.split('\n'):
            if any(keyword in line.lower() for keyword in ['sony', 'dualsense', 'wireless controller', 'gamepad']):
                print(f"  Found: {line}")
                found_controller = True
        if not found_controller:
            print("  No game controllers found in USB devices")
    else:
        print(f"  Could not check USB devices: {stderr}")
        if "No such file or directory" in stderr or "Permission denied" in stderr:
            print("  NOTE: USB subsystem might be disabled")
            print("  NOTE: Check /boot/config.txt for USB-related overlays")
    
    # Check Bluetooth devices - look for CONNECTED devices only
    print("\nBluetooth devices:")
    stdout, stderr, returncode = run_command_safely(['bluetoothctl', 'devices'], timeout=3)
    if returncode == 0:
        bt_devices = stdout
        found_connected_controller = False
        found_paired_controller = False
        
        for line in bt_devices.split('\n'):
            if any(keyword in line.lower() for keyword in ['sony', 'dualsense', 'wireless controller', 'gamepad']):
                # Extract MAC address
                parts = line.split()
                if len(parts) >= 2:
                    mac_address = parts[1]
                    
                    # Check if this device is connected
                    info_stdout, info_stderr, info_returncode = run_command_safely(
                        ['bluetoothctl', 'info', mac_address], timeout=2
                    )
                    
                    if info_returncode == 0 and 'Connected: yes' in info_stdout:
                        print(f"  CONNECTED: {line}")
                        found_connected_controller = True
                    else:
                        print(f"  PAIRED (not connected): {line}")
                        found_paired_controller = True
        
        if not found_connected_controller and not found_paired_controller:
            print("  No game controllers found in Bluetooth devices")
        elif not found_connected_controller and found_paired_controller:
            print("  NOTE: Found paired controllers but none are connected")
            print("  NOTE: Use 'bluetoothctl connect [MAC_ADDRESS]' to connect")
    else:
        print(f"  Could not check Bluetooth devices: {stderr}")
        if "No such file or directory" in stderr or "Connection refused" in stderr:
            print("  NOTE: Bluetooth might be disabled in device tree overlay")
            print("  NOTE: Check /boot/config.txt for 'dtoverlay=disable-bt' or similar")
            print("  NOTE: This is fine if you're using USB connection")
        elif "timed out" in stderr:
            print("  NOTE: Bluetooth daemon might not be running")
            print("  NOTE: Try: sudo systemctl start bluetooth")
    
    # Check input devices
    print("\nInput devices:")
    stdout, stderr, returncode = run_command_safely(['ls', '/dev/input/js*'], timeout=3)
    if returncode == 0 and stdout.strip():
        print("  Joystick devices:")
        for device in stdout.strip().split('\n'):
            if device:  # Only print non-empty lines
                print(f"    {device}")
    else:
        print("  No joystick devices found")
        # Only show diagnostic info if there was an error checking
        if returncode != 0:
            print("  NOTE: This might indicate:")
            print("     - USB disabled in device tree")
            print("     - Missing joystick drivers")

def print_troubleshooting_tips():
    """Print helpful troubleshooting tips."""
    print("\n" + "="*60)
    print("TROUBLESHOOTING TIPS")
    print("="*60)
    print("If controller is not detected:")
    print()
    print("USB Connection:")
    print("  - Connect controller via USB-C cable")
    print("  - Check if USB is enabled: cat /boot/config.txt | grep -i usb")
    print("  - Remove any 'dtoverlay=disable-usb' from /boot/config.txt")
    print()
    print("Bluetooth Connection:")
    print("  - Enable Bluetooth: sudo systemctl enable bluetooth")
    print("  - Start Bluetooth: sudo systemctl start bluetooth")
    print("  - Remove any 'dtoverlay=disable-bt' from /boot/config.txt")
    print("  - Put controller in pairing mode: Hold PS + Create buttons")
    print()
    print("System Checks:")
    print("  - Reboot after changing /boot/config.txt")
    print("  - Check if pygame is installed: pip install pygame")
    print("  - Verify controller works on another device")
    print("="*60)

if __name__ == "__main__":
    # Track if we found controllers at system level
    system_controllers_found = False
    
    # Check system-level controllers
    check_system_controllers()
    
    # Check pygame-level controllers
    pygame_controllers_found = False
    
    # Set display environment for headless systems
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    
    # Initialize pygame
    pygame.init()
    pygame.joystick.init()
    
    # Check for controllers
    joystick_count = pygame.joystick.get_count()
    if joystick_count > 0:
        pygame_controllers_found = True
    
    # Test controller functionality
    test_controller_functionality()
    
    # Only show troubleshooting if no controllers found at either level
    if not pygame_controllers_found:
        print_troubleshooting_tips() 